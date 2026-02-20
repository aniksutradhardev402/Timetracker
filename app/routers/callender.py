from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, date, time
from app.database import get_session
from app.models import TimeBlock
from app.schemas import TimeBlockCreate

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.post("/block")
def create_time_block(block: TimeBlockCreate, session: Session = Depends(get_session)):
    # --- Guard: end_time must be after start_time ---
    if block.end_time <= block.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    # --- Constraint 1: Only ONE block per task per day ---
    day_start = datetime.combine(block.start_time.date(), time.min)
    day_end = datetime.combine(block.start_time.date(), time.max)
    
    task_check = select(TimeBlock).where(
        TimeBlock.task_id == block.task_id,
        TimeBlock.start_time >= day_start,
        TimeBlock.start_time <= day_end
    )
    if session.exec(task_check).first():
        raise HTTPException(status_code=400, detail="This task already has a block today.")

    # --- Constraint 2: No Overlapping Blocks (ALL tasks, globally) ---
    overlap_check = select(TimeBlock).where(
        TimeBlock.start_time < block.end_time,
        TimeBlock.end_time > block.start_time
    )
    conflicting = session.exec(overlap_check).first()
    if conflicting:
        s = conflicting.start_time.strftime("%H:%M")
        e = conflicting.end_time.strftime("%H:%M")
        raise HTTPException(
            status_code=400,
            detail=f"Overlaps with an existing block ({s}–{e}). Pick a different time slot."
        )

    # --- SAVE ---
    db_block = TimeBlock(**block.model_dump())
    session.add(db_block)
    session.commit()
    session.refresh(db_block)
    return db_block

@router.get("/blocks")
def get_blocks(start: datetime, end: datetime, session: Session = Depends(get_session)):
    statement = select(TimeBlock).where(TimeBlock.start_time >= start, TimeBlock.start_time <= end)
    return session.exec(statement).all()

@router.delete("/block/{block_id}")
def delete_time_block(block_id: int, session: Session = Depends(get_session)):
    db_block = session.get(TimeBlock, block_id)
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")
    session.delete(db_block)
    session.commit()
    return {"status": "deleted"}