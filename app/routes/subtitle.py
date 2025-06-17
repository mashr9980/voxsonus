# app/routes/subtitle.py
from fastapi import APIRouter, HTTPException, Depends, status
import asyncpg
from app.core.database import get_db_connection
from app.core.security import get_current_active_user
from app.models.order import OrderStatus, PaymentStatus
from app.core import storage
from fastapi.responses import FileResponse
from app.core.config import settings
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{subtitle_file_id}/download")
async def download_subtitle_file(
    subtitle_file_id: int,
    conn: asyncpg.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_active_user)
):
    try:
        # Get subtitle file and verify ownership
        subtitle_file = await conn.fetchrow("""
            SELECT sf.*, v.order_id 
            FROM subtitle_files sf
            JOIN videos v ON sf.video_id = v.id
            JOIN orders o ON v.order_id = o.id
            WHERE sf.id = $1 AND o.user_id = $2
        """, subtitle_file_id, current_user["id"])
        
        if not subtitle_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtitle file not found"
            )
        
        file_key = subtitle_file["file_path"]
        if settings.USE_OBJECT_STORAGE:
            url = storage.generate_presigned_url(file_key, 3600)
            return {"download_url": url}
        else:
            if not os.path.exists(file_key):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
            return FileResponse(file_key, filename=os.path.basename(file_key))
    except Exception as e:
        logger.error(f"Error downloading subtitle file: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download subtitle file"
        )