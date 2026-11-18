from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def log_audit_event(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[uuid.UUID] = None,
    role: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Appends an immutable audit log record for HIPAA compliance.
    Tracks every read, write, update, or deletion of Protected Health Information (PHI).
    """
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        role=role or "SYSTEM",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "N/A",
        ip_address=ip_address or "127.0.0.1",
        details=details or {},
    )
    db.add(audit_entry)
    # Flushed as part of the current or outer transaction
    await db.flush()
    return audit_entry
