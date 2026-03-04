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
    is_streak: bool = False

class TaskUpdate(BaseModel):
    is_completed: Optional[bool] = None
    is_streak: Optional[bool] = None

class TaskRead(TaskCreate):
    id: int
    is_completed: bool
    is_streak: bool
    created_at: datetime

class TimeBlockCreate(BaseModel):
    task_id: int
    start_time: datetime
    end_time: datetime

class TimeBlockRead(TimeBlockCreate):
    id: int

class ActiveTimerCreate(BaseModel):
    task_id: int
    start_time: datetime

class ActiveTimerRead(BaseModel):
    task_id: int
    start_time: Optional[datetime]
    accumulated_seconds: int
    is_paused: bool



class PieChartData(BaseModel):
    name: str       
    value: int      
    color: str      

class BarChartData(BaseModel):
    date: str                   
    categories: Dict[str, int]  

class TaskBreakdownData(BaseModel):
    task: str       
    minutes: int
    color: str      

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
