# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, subtitle, users, admin, orders, payments, notification, tasks, dashboard
from app.core.config import settings
from app.core.database import create_tables
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(
    title="AI Subtitles Platform API",
    description="API for AI-powered subtitle generation platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await create_tables()

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(subtitle.router, prefix="/api/subtitles", tags=["Subtitles"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(notification.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(tasks.router, prefix="/api/celery", tags=["Celery"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

@app.get("/")
async def root():
    return {"message": "AI Subtitles Platform API"}
