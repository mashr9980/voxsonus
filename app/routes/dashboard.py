from fastapi import APIRouter, Depends, HTTPException, status
import asyncpg
from typing import List
from datetime import datetime
import os
from app.core.database import get_db_connection
from app.core.security import get_current_active_user
from app.models.dashboard import (
    DashboardStats,
    RecentOrderItem,
    SubtitleDownloadItem,
)
from app.models.order import OrderStatus, PaymentStatus
from app.core.config import settings
from app.core import storage
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview", response_model=DashboardStats)
async def dashboard_overview(
    conn: asyncpg.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_active_user),
):
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS total_orders,
                COUNT(*) FILTER (WHERE status = 'processing') AS processing_orders,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
                COALESCE(SUM(total_amount) FILTER (WHERE payment_status = 'paid'), 0) AS total_spent
            FROM orders
            WHERE user_id = $1
            """,
            current_user["id"],
        )
        return {
            "total_orders": row["total_orders"],
            "processing_orders": row["processing_orders"],
            "completed_orders": row["completed_orders"],
            "total_spent": float(row["total_spent"]),
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard overview",
        )


@router.get("/recent-orders", response_model=List[RecentOrderItem])
async def recent_orders(
    limit: int = 5,
    conn: asyncpg.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_active_user),
):
    try:
        orders = await conn.fetch(
            """
            SELECT id, status, total_amount, created_at, total_duration
            FROM orders
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            current_user["id"],
            limit,
        )
        result: List[RecentOrderItem] = []
        for order in orders:
            video = await conn.fetchrow(
                "SELECT original_filename, duration FROM videos WHERE order_id = $1 ORDER BY id LIMIT 1",
                order["id"],
            )
            result.append(
                RecentOrderItem(
                    id=order["id"],
                    video_title=video["original_filename"] if video else "",
                    status=order["status"],
                    price=float(order["total_amount"]),
                    date=order["created_at"],
                    duration=order["total_duration"],
                )
            )
        return result
    except Exception as e:
        logger.error(f"Error fetching recent orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent orders",
        )


@router.get("/downloads", response_model=List[SubtitleDownloadItem])
async def available_downloads(
    conn: asyncpg.Connection = Depends(get_db_connection),
    current_user: dict = Depends(get_current_active_user),
):
    try:
        rows = await conn.fetch(
            """
            SELECT sf.id, sf.file_path, v.original_filename
            FROM subtitle_files sf
            JOIN videos v ON sf.video_id = v.id
            JOIN orders o ON v.order_id = o.id
            WHERE o.user_id = $1
              AND o.status = $2
              AND sf.file_format = 'srt'
            ORDER BY sf.created_at DESC
            """,
            current_user["id"],
            OrderStatus.COMPLETED,
        )
        items: List[SubtitleDownloadItem] = []
        for r in rows:
            file_key = r["file_path"]
            url = storage.generate_presigned_url(file_key, 3600)
            if settings.USE_OBJECT_STORAGE:
                try:
                    head = storage._s3_client.head_object(Bucket=storage.BUCKET, Key=file_key)
                    file_size = head.get("ContentLength", 0)
                except Exception:
                    file_size = 0
            else:
                file_size = os.path.getsize(file_key) if os.path.exists(file_key) else 0
            items.append(
                SubtitleDownloadItem(
                    id=r["id"],
                    download_url=url,
                    subtitle_file_name=os.path.basename(file_key),
                    video_name=r["original_filename"],
                    file_size=file_size,
                )
            )
        return items
    except Exception as e:
        logger.error(f"Error fetching downloads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch downloads",
        )
