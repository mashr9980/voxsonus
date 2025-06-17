from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    order_id: Optional[int] = None
    message: str
    is_read: bool
    created_at: datetime
