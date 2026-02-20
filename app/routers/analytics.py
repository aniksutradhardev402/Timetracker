from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from datetime import datetime, date, timedelta
from typing import List

from app.database import get_session
from app.models import TimeBlock, Task, Category
from app.schemas import DashboardReport, PieChartData, BarChartData, TaskBreakdownData, TaskStreakReport

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardReport)
def get_dashboard_data(
    start_date: datetime = Query(..., description="Start of range"),
    end_date: datetime = Query(..., description="End of range"),
    session: Session = Depends(get_session)
):
    statement = select(TimeBlock).where(
        TimeBlock.start_time >= start_date,
        TimeBlock.end_time <= end_date
    )
    blocks = session.exec(statement).all()

    total_minutes = 0
    pie_data: dict = {}      # {cat_name: {name, value, color}}
    bar_data: dict = {}      # {date_str: {cat_name: minutes}}
    task_data: dict = {}     # {task_title: {minutes, color}}

    for block in blocks:
        duration = int((block.end_time - block.start_time).total_seconds() // 60)
        total_minutes += duration

        task_title = block.task.title if block.task else "Unknown"
        cat_name   = block.task.category.name      if (block.task and block.task.category) else "Uncategorized"
        cat_color  = block.task.category.color_hex if (block.task and block.task.category) else "#CCCCCC"

        # -- Pie chart (by category) --
        if cat_name not in pie_data:
            pie_data[cat_name] = {"name": cat_name, "value": 0, "color": cat_color}
        pie_data[cat_name]["value"] += duration

        # -- Bar chart (by date × category) --
        block_date_str = block.start_time.date().isoformat()
        bar_data.setdefault(block_date_str, {})
        bar_data[block_date_str][cat_name] = bar_data[block_date_str].get(cat_name, 0) + duration

        # -- Task breakdown (by task) --
        if task_title not in task_data:
            task_data[task_title] = {"minutes": 0, "color": cat_color}
        task_data[task_title]["minutes"] += duration

    return DashboardReport(
        total_minutes=total_minutes,
        pie_chart=list(pie_data.values()),
        bar_chart=[{"date": d, "categories": cats} for d, cats in sorted(bar_data.items())],
        task_breakdown=[
            TaskBreakdownData(task=title, minutes=v["minutes"], color=v["color"])
            for title, v in sorted(task_data.items(), key=lambda x: -x[1]["minutes"])
        ]
    )


@router.get("/streak/{task_id}", response_model=TaskStreakReport)
def get_task_streak(task_id: int, session: Session = Depends(get_session)):
    """
    Calculates your current daily consistency streak for a specific task.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    statement = select(TimeBlock).where(TimeBlock.task_id == task_id)
    blocks = session.exec(statement).all()

    if not blocks:
        return TaskStreakReport(
            task_id=task.id, task_title=task.title, current_streak_days=0,
            total_time_spent_minutes=0, tracked_days_count=0
        )

    today = datetime.utcnow().date()
    total_time = sum(int((b.end_time - b.start_time).total_seconds() // 60) for b in blocks)

    # Only count past + today dates (ignore future seed data)
    unique_dates = sorted(
        list(set(b.start_time.date() for b in blocks if b.start_time.date() <= today)),
        reverse=True
    )
    
    current_streak = 0
    if unique_dates and (unique_dates[0] == today or unique_dates[0] == today - timedelta(days=1)):
        current_streak = 1
        current_date_to_check = unique_dates[0]
        for i in range(1, len(unique_dates)):
            if unique_dates[i] == current_date_to_check - timedelta(days=1):
                current_streak += 1
                current_date_to_check = unique_dates[i]
            else:
                break

    return TaskStreakReport(
        task_id=task.id,
        task_title=task.title,
        current_streak_days=current_streak,
        total_time_spent_minutes=total_time,
        tracked_days_count=len(unique_dates)   # past + today only
    )