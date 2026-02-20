from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, date, time
from app.database import get_session
from app.models import Task ,TimeBlock
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.schemas import TimeBlockCreate
router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/block")
def create_time_block(block: TimeBlockCreate, session: Session = Depends(get_session)):
    # 1. Check Constraint: Only one time block allowed per task for a day
    day_start = datetime.combine(block.start_time.date(), time.min)
    day_end = datetime.combine(block.start_time.date(), time.max)
    
    stmt_task_day = select(TimeBlock).where(
        TimeBlock.task_id == block.task_id,
        TimeBlock.start_time >= day_start,
        TimeBlock.start_time <= day_end
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

    # Clear only today's blocks for this task
    day_start = datetime.combine(date.today(), time.min)
    day_end = datetime.combine(date.today(), time.max)
    
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