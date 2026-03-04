from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import List
from datetime import datetime, date, time, timedelta
from app.database import get_session
from app.models import Task ,TimeBlock
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.schemas import TimeBlockCreate
from app.core.config import OFFSET_HOURS
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# @router.post("/block")
# def create_time_block(block: TimeBlockCreate, session: Session = Depends(get_session)):
#     effective_date = (block.start_time - timedelta(hours=OFFSET_HOURS)).date()
#     day_start = datetime.combine(effective_date, time(OFFSET_HOURS, 0))
#     day_end = day_start + timedelta(days=1)
    
#     stmt_task_day = select(TimeBlock).where(
#         TimeBlock.task_id == block.task_id,
#         TimeBlock.start_time >= day_start,
#         TimeBlock.start_time < day_end
#     )
#     if session.exec(stmt_task_day).first():
#         raise HTTPException(status_code=400, detail="This task already has a logged block today.")

#     stmt_overlap = select(TimeBlock).where(
#         TimeBlock.start_time < block.end_time,
#         TimeBlock.end_time > block.start_time
#     )
#     if session.exec(stmt_overlap).first():
#         raise HTTPException(status_code=400, detail="This overlaps with an existing time block on your calendar.")

#     db_block = TimeBlock(**block.model_dump())
#     session.add(db_block)
#     session.commit()
#     session.refresh(db_block)
#     return db_block

@router.post("/", response_model=TaskRead)
def create_task(task: TaskCreate, session: Session = Depends(get_session)):
    stmt = select(Task).where(
        func.lower(Task.title) == task.title.lower(),
        Task.category_id == task.category_id
    )
    existing_task = session.exec(stmt).first()
    
    if existing_task:
        existing_task.created_at = datetime.utcnow()
        existing_task.is_completed = False
        session.add(existing_task)
        session.commit()
        session.refresh(existing_task)
        return existing_task

    db_task = Task(**task.model_dump())
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
    
    if task_update.is_completed is not None:
        db_task.is_completed = task_update.is_completed
    if task_update.is_streak is not None:
        db_task.is_streak = task_update.is_streak
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.delete("/{task_id}")
def delete_task(task_id: int, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

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

    all_history = session.exec(select(TimeBlock).where(TimeBlock.task_id == task_id)).all()
    if not all_history:
        session.delete(db_task)
        
    session.commit()
    return {"status": "success"}

@router.delete("/force/{task_id}")
def force_delete_task(task_id: int, session: Session = Depends(get_session)):
    db_task = session.get(Task, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    all_history = session.exec(select(TimeBlock).where(TimeBlock.task_id == task_id)).all()
    for b in all_history:
        session.delete(b)
        
    session.delete(db_task)
    session.commit()
    return {"status": "success"}