from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class TaskInfo(BaseModel):
    id: str
    name: Optional[str] = None
    status: Optional[str] = None
    worker: Optional[str] = None
    args: Optional[str] = None
    kwargs: Optional[str] = None
    eta: Optional[str] = None
    time_start: Optional[float] = None
    runtime: Optional[float] = None


class TaskDetail(TaskInfo):
    result: Optional[Any] = None
    date_done: Optional[datetime] = None
    traceback: Optional[str] = None
