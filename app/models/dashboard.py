from pydantic import BaseModel
from datetime import datetime

class DashboardStats(BaseModel):
    total_orders: int
    processing_orders: int
    completed_orders: int
    total_spent: float

class RecentOrderItem(BaseModel):
    id: int
    video_title: str
    status: str
    price: float
    date: datetime
    duration: int

class SubtitleDownloadItem(BaseModel):
    id: int
    download_url: str
    subtitle_file_name: str
    video_name: str
    file_size: int
