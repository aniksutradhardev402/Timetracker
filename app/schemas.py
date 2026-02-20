from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, date


class CategoryCreate(BaseModel):
    name: str
    color_hex: str

class CategoryRead(CategoryCreate):
    id: int

class TaskCreate(BaseModel):
    title: str
    category_id: Optional[int] = None

class TaskUpdate(BaseModel):
    is_completed: bool

class TaskRead(TaskCreate):
    id: int
    is_completed: bool
    created_at: datetime

class TimeBlockCreate(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime

class TimeBlockRead(TimeBlockCreate):
    id: int


# ── Analytics schemas ────────────────────────────────────────────────

class PieChartData(BaseModel):
    name: str       # category name
    value: int      # minutes
    color: str      # hex color

class BarChartData(BaseModel):
    date: str                   # ISO date string
    categories: Dict[str, int]  # {category_name: minutes}

class TaskBreakdownData(BaseModel):
    task: str       # task title
    minutes: int
    color: str      # category hex color

class DashboardReport(BaseModel):
    total_minutes: int
    pie_chart: List[PieChartData]
    bar_chart: List[BarChartData]
    task_breakdown: List[TaskBreakdownData]

class TaskStreakReport(BaseModel):
    task_id: int
    task_title: str
    current_streak_days: int
    total_time_spent_minutes: int
    tracked_days_count: int
