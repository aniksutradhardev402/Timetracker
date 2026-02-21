from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, date, time, timedelta
from app.database import get_session
from app.models import Task ,TimeBlock
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.schemas import TimeBlockCreate
from app.core.config import OFFSET_HOURS
router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/block")
def create_time_block(block: TimeBlockCreate, session: Session = Depends(get_session)):
    # 1. Check Constraint: Only one time block allowed per task for a day (respecting offset)
    effective_date = (block.start_time - timedelta(hours=OFFSET_HOURS)).date()
    day_start = datetime.combine(effective_date, time(OFFSET_HOURS, 0))
    day_end = day_start + timedelta(days=1)
    
    stmt_task_day = select(TimeBlock).where(
        TimeBlock.task_id == block.task_id,
        TimeBlock.start_time >= day_start,
        TimeBlock.start_time < day_end
    )
    if session.exec(stmt_task_day).first():
        raise HTTPException(status_code=400, detail="This task already has a logged block today.")

    # 2. Check Constraint: No overlapping blocks (for ANY task)
    # Standard overlap math: Existing Start < New End AND Existing End > New Start
    stmt_overlap = select(TimeBlock).where(
        TimeBlock.start_time < block.end_time,
        TimeBlock.end_time > block.start_time
    )
    if session.exec(stmt_overlap).first():
        raise HTTPException(status_code=400, detail="This overlaps with an existing time block on your calendar.")

    # 3. If it passes the checks, save it
    from app.models import TimeBlock # Ensure this is imported
    db_block = TimeBlock(**block.dict())
    session.add(db_block)
    session.commit()
    session.refresh(db_block)
    return db_block

@router.post("/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    db_task = Task(**task.dict())
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/", response_model=List[TaskRead])
def get_tasks(session: Session = Depends(get_session)):
    return session.exec(select(Task)).all()

@router.put("/{task_id}", response_model=TaskRead)
def toggle_task_completion(task_id: int, task_update: TaskUpdate, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_task.is_completed = task_update.is_completed
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Clear only today's blocks for this task (respecting offset)
    now = datetime.now()
    effective_today = (now - timedelta(hours=OFFSET_HOURS)).date()
    day_start = datetime.combine(effective_today, time(OFFSET_HOURS, 0))
    day_end = day_start + timedelta(days=1)
    
    today_blocks = session.exec(select(TimeBlock).where(
        TimeBlock.task_id == task_id,
        TimeBlock.start_time >= day_start,
        TimeBlock.start_time <= day_end
    )).all()
    
    for b in today_blocks:
        session.delete(b)

    # Only delete the actual Task if it has zero history left
    all_history = session.exec(select(TimeBlock).where(TimeBlock.task_id == task_id)).all()
    if not all_history:
        session.delete(db_task)
        
    session.commit()
    return {"status": "success"}