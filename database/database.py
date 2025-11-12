"""
PostgreSQL database manager for Clinical Trials Platform
Complete CRUD operations with connection pooling
"""
import asyncpg
import json
from typing import Dict, List, Optional
from datetime import datetime, date
import uuid
import os


class PostgresDatabase:
    """PostgreSQL database manager with all operations"""

    def __init__(self, redis_client=None):
        self.pool = None
        self.redis = redis_client  # Optional Redis for caching

    async def connect(self):
        """Initialize connection pool"""
        # For local development
        DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://clinical_user:clinical_pass@localhost:5432/clinical_trials"
        )

        # For AWS RDS (commented for reference)
        # DATABASE_URL = "postgresql://admin:password@clinical-db.cluster-xxx.rds.amazonaws.com:5432/clinical_trials"

        self.pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=5,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60
        )

        print("✅ PostgreSQL connected")

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            print("PostgreSQL connection closed")

    # ========== PATIENT OPERATIONS ==========

    async def create_patient(self, patient_data: Dict) -> str:
        """Create new patient with validation"""
        async with self.pool.acquire() as conn:
            try:
                patient_id = await conn.fetchval("""
                    INSERT INTO patients (
                        subject_number, site_id, protocol_id,
                        enrollment_date, treatment_arm, demographics
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING patient_id
                """,
                    patient_data['subject_number'],
                    patient_data['site_id'],
                    patient_data['protocol_id'],
                    date.fromisoformat(patient_data['enrollment_date']) if isinstance(patient_data['enrollment_date'], str) else patient_data['enrollment_date'],
                    patient_data.get('treatment_arm'),
                    json.dumps(patient_data.get('demographics', {}))
                )

                # Clear cache
                if self.redis:
                    await self.redis.delete(f"patients:{patient_data['site_id']}")

                # Log event
                await self.log_event('patient_created', {
                    'patient_id': str(patient_id),
                    'site_id': patient_data['site_id']
                })

                return str(patient_id)

            except asyncpg.UniqueViolationError:
                raise ValueError(f"Subject number {patient_data['subject_number']} already exists")

    async def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get patient with caching"""
        # Check Redis cache first
        if self.redis:
            cached = await self.redis.get(f"patient:{patient_id}")
            if cached:
                return json.loads(cached)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT p.*,
                       COUNT(DISTINCT v.vital_id) as vital_count,
                       COUNT(DISTINCT d.document_id) as document_count,
                       MAX(v.measurement_time) as last_vital
                FROM patients p
                LEFT JOIN vital_signs v ON p.patient_id = v.patient_id
                LEFT JOIN documents d ON p.patient_id = d.patient_id
                WHERE p.patient_id = $1
                GROUP BY p.patient_id
            """, uuid.UUID(patient_id))

            if row:
                patient = dict(row)
                # Convert UUID and dates to strings for JSON
                patient['patient_id'] = str(patient['patient_id'])
                patient['enrollment_date'] = patient['enrollment_date'].isoformat()
                if patient.get('last_vital'):
                    patient['last_vital'] = patient['last_vital'].isoformat()

                # Cache for 5 minutes
                if self.redis:
                    await self.redis.setex(
                        f"patient:{patient_id}",
                        300,
                        json.dumps(patient, default=str)
                    )

                return patient
            return None

    async def search_patients(self, filters: Dict) -> List[Dict]:
        """Advanced patient search with filters"""
        query = "SELECT * FROM patients WHERE 1=1"
        params = []
        param_count = 0

        if filters.get('site_id'):
            param_count += 1
            query += f" AND site_id = ${param_count}"
            params.append(filters['site_id'])

        if filters.get('protocol_id'):
            param_count += 1
            query += f" AND protocol_id = ${param_count}"
            params.append(filters['protocol_id'])

        if filters.get('status'):
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(filters['status'])

        query += " ORDER BY enrollment_date DESC LIMIT 100"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    # ========== DOCUMENT OPERATIONS (MongoDB Replacement) ==========

    async def store_document(self, document: Dict) -> str:
        """Store clinical document as JSON"""
        async with self.pool.acquire() as conn:
            doc_id = await conn.fetchval("""
                INSERT INTO documents (
                    patient_id, document_type, title, content, metadata, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING document_id
            """,
                uuid.UUID(document.get('patient_id')) if document.get('patient_id') else None,
                document['document_type'],
                document.get('title'),
                json.dumps(document['content']),
                json.dumps(document.get('metadata', {})),
                document.get('created_by', 'system')
            )

            # Invalidate cache
            if self.redis and document.get('patient_id'):
                await self.redis.delete(f"patient:{document['patient_id']}")

            return str(doc_id)

    async def search_documents(self, search_term: str, doc_type: Optional[str] = None) -> List[Dict]:
        """Full-text search in documents using PostgreSQL JSON search"""
        query = """
            SELECT document_id, patient_id, document_type, title,
                   content, created_at
            FROM documents
            WHERE content::text ILIKE $1
        """
        params = [f'%{search_term}%']

        if doc_type:
            query += " AND document_type = $2"
            params.append(doc_type)

        query += " ORDER BY created_at DESC LIMIT 50"

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]

    # ========== VITAL SIGNS OPERATIONS (Time-Series) ==========

    async def store_vitals(self, patient_id: str, vitals: Dict) -> str:
        """Store vital signs data"""
        async with self.pool.acquire() as conn:
            vital_id = await conn.fetchval("""
                INSERT INTO vital_signs (
                    patient_id, visit_date, measurement_time,
                    systolic_bp, diastolic_bp, heart_rate,
                    temperature, respiratory_rate, data_batch
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING vital_id
            """,
                uuid.UUID(patient_id),
                date.fromisoformat(vitals['visit_date']) if isinstance(vitals['visit_date'], str) else vitals['visit_date'],
                datetime.fromisoformat(vitals['measurement_time']) if isinstance(vitals['measurement_time'], str) else vitals['measurement_time'],
                vitals.get('systolic_bp'),
                vitals.get('diastolic_bp'),
                vitals.get('heart_rate'),
                vitals.get('temperature'),
                vitals.get('respiratory_rate'),
                json.dumps(vitals.get('additional_data', {}))
            )

            # Clear vitals cache
            if self.redis:
                await self.redis.delete(f"vitals:{patient_id}:*")

            return str(vital_id)

    async def get_patient_vitals(self, patient_id: str, days: int = 30) -> List[Dict]:
        """Get patient vitals with caching"""
        cache_key = f"vitals:{patient_id}:{days}"

        # Check cache
        if self.redis:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM vital_signs
                WHERE patient_id = $1
                AND measurement_time > CURRENT_TIMESTAMP - ($2 || ' days')::INTERVAL
                ORDER BY measurement_time DESC
            """, uuid.UUID(patient_id), days)

            vitals = []
            for row in rows:
                vital = dict(row)
                vital['vital_id'] = str(vital['vital_id'])
                vital['patient_id'] = str(vital['patient_id'])
                vital['visit_date'] = vital['visit_date'].isoformat()
                vital['measurement_time'] = vital['measurement_time'].isoformat()
                vitals.append(vital)

            # Cache for 5 minutes
            if self.redis:
                await self.redis.setex(cache_key, 300, json.dumps(vitals, default=str))

            return vitals

    # ========== MCP CONTEXT OPERATIONS ==========

    async def update_mcp_context(self, agent_id: str, context: Dict):
        """Update MCP agent context"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO mcp_context (agent_id, context_type, context_data, last_updated)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (agent_id)
                DO UPDATE SET
                    context_data = $3,
                    last_updated = CURRENT_TIMESTAMP
            """,
                agent_id,
                context.get('type', 'general'),
                json.dumps(context)
            )

    async def get_mcp_context(self, agent_id: str) -> Optional[Dict]:
        """Get MCP agent context"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM mcp_context WHERE agent_id = $1",
                agent_id
            )
            return dict(row) if row else None

    # ========== ANALYTICS OPERATIONS ==========

    async def get_site_analytics(self, site_id: str) -> Dict:
        """Get site-level analytics"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT p.patient_id) as total_patients,
                    COUNT(DISTINCT CASE WHEN p.status = 'ENROLLED' THEN p.patient_id END) as active_patients,
                    AVG(EXTRACT(epoch FROM (NOW() - p.enrollment_date))/86400)::INT as avg_days_enrolled,
                    COUNT(DISTINCT v.vital_id) as total_vitals,
                    COUNT(DISTINCT d.document_id) as total_documents,
                    MAX(v.measurement_time) as last_vital_recorded
                FROM patients p
                LEFT JOIN vital_signs v ON p.patient_id = v.patient_id
                LEFT JOIN documents d ON p.patient_id = d.patient_id
                WHERE p.site_id = $1
            """, site_id)

            return dict(stats) if stats else {}

    # ========== EVENT LOGGING ==========

    async def log_event(self, event_type: str, payload: Dict, user_id: str = None):
        """Log audit event for HIPAA compliance"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_events (event_type, payload, user_id, timestamp)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            """,
                event_type,
                json.dumps(payload),
                user_id
            )

    async def get_audit_trail(self, entity_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit trail"""
        query = "SELECT * FROM audit_events"
        params = []

        if entity_id:
            query += " WHERE entity_id = $1"
            params.append(uuid.UUID(entity_id))

        query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            events = []
            for row in rows:
                event = dict(row)
                event['event_id'] = str(event['event_id'])
                if event.get('entity_id'):
                    event['entity_id'] = str(event['entity_id'])
                event['timestamp'] = event['timestamp'].isoformat()
                events.append(event)
            return events


# Global database instance
db = PostgresDatabase()
