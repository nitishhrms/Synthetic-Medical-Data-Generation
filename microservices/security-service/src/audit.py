"""
HIPAA-Compliant Audit Logging
All access to PHI must be logged with immutable audit trail
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import hashlib
import models
import database
from sqlalchemy.orm import Session

def _generate_integrity_hash(log_entry: Dict) -> str:
    """Generate hash for log integrity verification"""
    log_str = json.dumps(log_entry, sort_keys=True)
    return hashlib.sha256(log_str.encode()).hexdigest()

async def log_audit_event(
    db: Session,
    user_id: str,
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None
) -> models.AuditLog:
    """Create immutable audit log entry"""
    log_entry_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "resource": resource,
        "details": details or {},
    }

    integrity_hash = _generate_integrity_hash(log_entry_data)

    log_entry = models.AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details or {},
        integrity_hash=integrity_hash
    )

    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return log_entry

async def get_audit_logs(
    db: Session,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    limit: int = 100
) -> List[models.AuditLog]:
    """Retrieve audit logs with filtering"""
    query = db.query(models.AuditLog)

    if user_id:
        query = query.filter(models.AuditLog.user_id == user_id)
    if action:
        query = query.filter(models.AuditLog.action == action)
    if resource:
        query = query.filter(models.AuditLog.resource == resource)

    return query.order_by(models.AuditLog.timestamp.desc()).limit(limit).all()
