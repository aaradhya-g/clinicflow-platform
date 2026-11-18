from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: Optional[uuid.UUID] = None
    role: str
    action: str
    resource_type: str
    resource_id: str
    ip_address: str
    details: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class AuditLogFilter(BaseModel):
    action: Optional[str] = None
    resource_type: Optional[str] = None
    role: Optional[str] = None
    limit: int = 50
    offset: int = 0
