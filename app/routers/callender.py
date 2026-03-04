from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import TimeBlock
from app.schemas import TimeBlockCreate
from app.core.config import OFFSET_HOURS
from datetime import datetime, date, time, timedelta

router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.post("/block")
def create_time_block(block: TimeBlockCreate, session: Session = Depends(get_session)):
    if block.end_time <= block.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    effective_date = (block.start_time - timedelta(hours=OFFSET_HOURS)).date()
    day_start = datetime.combine(effective_date, time(OFFSET_HOURS, 0))
    day_end = day_start + timedelta(days=1)

    overlap_check = select(TimeBlock).where(
        TimeBlock.start_time < block.end_time,
        TimeBlock.end_time > block.start_time
    )
    conflicting_blocks = session.exec(overlap_check).all()
    
    for conflict in conflicting_blocks:
        if conflict.start_time >= block.start_time and conflict.end_time <= block.end_time:
            session.delete(conflict)
        elif conflict.start_time >= block.start_time and conflict.start_time < block.end_time:
            conflict.start_time = block.end_time
            session.add(conflict)
        elif conflict.end_time > block.start_time and conflict.end_time <= block.end_time:
            conflict.end_time = block.start_time
            session.add(conflict)
        elif conflict.start_time < block.start_time and conflict.end_time > block.end_time:
            new_after_block = TimeBlock(
                task_id=conflict.task_id,
                start_time=block.end_time,
                end_time=conflict.end_time
            )
            conflict.end_time = block.start_time
            session.add(conflict)
            session.add(new_after_block)

    db_block = TimeBlock(**block.model_dump())
    session.add(db_block)
    session.commit()
    session.refresh(db_block)
    return db_block

@router.get("/blocks")
def get_blocks(start: datetime, end: datetime, session: Session = Depends(get_session)):
    statement = select(TimeBlock).where(TimeBlock.start_time >= start, TimeBlock.start_time <= end)
    return session.exec(statement).all()

@router.put("/block/{block_id}")
def update_time_block(block_id: int, block: TimeBlockCreate, session: Session = Depends(get_session)):
    db_block = session.get(TimeBlock, block_id)
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")

    if block.end_time <= block.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    overlap_check = select(TimeBlock).where(
        TimeBlock.id != block_id,
        TimeBlock.start_time < block.end_time,
        TimeBlock.end_time > block.start_time
    )
    conflicting_blocks = session.exec(overlap_check).all()
    
    for conflict in conflicting_blocks:
        if conflict.start_time >= block.start_time and conflict.end_time <= block.end_time:
            session.delete(conflict)
        elif conflict.start_time >= block.start_time and conflict.start_time < block.end_time:
            conflict.start_time = block.end_time
            session.add(conflict)
        elif conflict.end_time > block.start_time and conflict.end_time <= block.end_time:
            conflict.end_time = block.start_time
            session.add(conflict)
        elif conflict.start_time < block.start_time and conflict.end_time > block.end_time:
            new_after_block = TimeBlock(
                task_id=conflict.task_id,
                start_time=block.end_time,
                end_time=conflict.end_time
            )
            conflict.end_time = block.start_time
            session.add(conflict)
            session.add(new_after_block)

    db_block.task_id = block.task_id
    db_block.start_time = block.start_time
    db_block.end_time = block.end_time
    session.add(db_block)
    session.commit()
    session.refresh(db_block)
    return db_block

@router.delete("/block/{block_id}")
def delete_time_block(block_id: int, session: Session = Depends(get_session)):
    db_block = session.get(TimeBlock, block_id)
    if not db_block:
        raise HTTPException(status_code=404, detail="Block not found")
    session.delete(db_block)
    session.commit()
    return {"status": "deleted"}