from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List
from app.core.database import get_db_connection
from app.core.security import get_current_active_user
from app.core.utils import fetch_notifications
from app.models.notification import NotificationResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 100,
    conn: asyncpg.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_active_user),
):
    try:
        return await fetch_notifications(conn, current_user["id"], skip, limit)
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notifications",
        )
