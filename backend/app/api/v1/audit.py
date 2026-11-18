from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_admin
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead

router = APIRouter()


@router.get("/", response_model=List[AuditLogRead])
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by audit action (e.g. READ_PATIENT_EHR, CREATE_APPOINTMENT)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. PATIENT, APPOINTMENT, VITALS)"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    HIPAA Audit Log Explorer.
    Allows administrators to audit every PHI access and modification.
    Logs are strictly immutable and cannot be edited or deleted.
    """
    stmt = select(AuditLog)

    if action:
        stmt = stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if role:
        stmt = stmt.where(AuditLog.role == role)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return logs
