from contextlib import asynccontextmanager 
from app.database import init_db, get_session
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from app.models import ActiveTimer
from pydantic import BaseModel
from datetime import datetime
from app.routers import categories, tasks, callender
from app.routers import analytics, timer
from app.core.config import ALLOWED_ORIGINS, OFFSET_HOURS
from app.models import TimeBlock
from datetime import timedelta, time
import psutil
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database Tables...")
    init_db()
    yield


app = FastAPI(title="Daily Focus API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(tasks.router)
app.include_router(callender.router)
app.include_router(analytics.router)
app.include_router(timer.router)

@app.get("/")
def read_root():
    return {"status": "Database and API are connected and running!"}

@app.get("/system/stats")
def get_system_stats():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "process_cpu_percent": process.cpu_percent(interval=0.1),
        "total_memory_hz": psutil.virtual_memory().total,
        "available_memory_hz": psutil.virtual_memory().available,
        "process_memory_hz": mem_info.rss,
        "memory_percent": psutil.virtual_memory().percent
    }


