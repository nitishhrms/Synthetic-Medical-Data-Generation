"""
Shared Database Utilities for Microservices
Lightweight database connection management using asyncpg and Redis
"""
import os
import asyncpg
import redis.asyncio as redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Async PostgreSQL connection manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://clinical_user:clinical_pass@postgres:5432/clinical_trials"
        )

    async def connect(self, max_retries=5, retry_delay=2):
        """Initialize database connection pool with retry logic"""
        import asyncio

        for attempt in range(max_retries):
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=30
                )
                logger.info("Database connection pool created successfully")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Failed to connect to database (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                    logger.info("Service will continue without database connection")
                    # Don't raise - allow service to start without DB for health checks

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args):
        """Execute a query that doesn't return results"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Execute a query and fetch all results"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Execute a query and fetch one result"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Execute a query and fetch a single value"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


class CacheConnection:
    """Async Redis cache manager"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.enabled = True

    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Running without cache.")
            self.enabled = False
            self.client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.enabled or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: str, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        if not self.enabled or not self.client:
            return False
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled or not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.enabled or not self.client:
            return 0
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error: {e}")
            return 0


# Global instances
db = DatabaseConnection()
cache = CacheConnection()


    async def create_tables(self):
        """Create necessary tables if they don't exist"""
        if not self.pool:
            return

        query = """
        CREATE TABLE IF NOT EXISTS generated_datasets (
            id SERIAL PRIMARY KEY,
            dataset_name VARCHAR(255) NOT NULL,
            dataset_type VARCHAR(50) NOT NULL,
            data JSONB NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_dataset_type ON generated_datasets(dataset_type);
        CREATE INDEX IF NOT EXISTS idx_created_at ON generated_datasets(created_at DESC);
        """
        try:
            await self.execute(query)
            logger.info("Database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize tables: {e}")

    async def save_dataset(self, name: str, dtype: str, data: list, metadata: dict = None) -> int:
        """Save a generated dataset"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        import json
        query = """
        INSERT INTO generated_datasets (dataset_name, dataset_type, data, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        # Ensure data is JSON serializable
        data_json = json.dumps(data)
        metadata_json = json.dumps(metadata) if metadata else None
        
        return await self.fetchval(query, name, dtype, data_json, metadata_json)

    async def get_latest_dataset(self, dtype: str):
        """Get the most recently generated dataset of a specific type"""
        if not self.pool:
            raise RuntimeError("Database not connected")
            
        query = """
        SELECT id, dataset_name, dataset_type, data, metadata, created_at
        FROM generated_datasets
        WHERE dataset_type = $1
        ORDER BY created_at DESC
        LIMIT 1
        """
        row = await self.fetchrow(query, dtype)
        if not row:
            return None
            
        import json
        return {
            "id": row["id"],
            "dataset_name": row["dataset_name"],
            "dataset_type": row["dataset_type"],
            "data": json.loads(row["data"]) if isinstance(row["data"], str) else row["data"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] and isinstance(row["metadata"], str) else row["metadata"],
            "created_at": row["created_at"]
        }

async def startup_db():
    """Startup event handler for FastAPI"""
    await db.connect()
    await db.create_tables()
    await cache.connect()


async def shutdown_db():
    """Shutdown event handler for FastAPI"""
    await db.disconnect()
    await cache.disconnect()
