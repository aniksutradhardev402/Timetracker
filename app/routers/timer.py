from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime, time, timedelta

from app.database import get_session
from app.models import ActiveTimer, TimeBlock
from app.schemas import ActiveTimerCreate, ActiveTimerRead
from app.core.config import OFFSET_HOURS

router = APIRouter(prefix="/timer", tags=["timer"])

@router.post("/start")
def start_timer(timer_in: ActiveTimerCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(ActiveTimer)).all()
    for e in existing:
        session.delete(e)
    session.commit()
    
    new_timer = ActiveTimer(task_id=timer_in.task_id, start_time=timer_in.start_time, accumulated_seconds=0)
    session.add(new_timer)
    session.commit()
    return {"status": "started"}

@router.get("/active", response_model=None)
def get_active_timer(session: Session = Depends(get_session)):
    timer = session.exec(select(ActiveTimer)).first()
    if timer:
        now = datetime.now()
        is_paused = timer.start_time is None
        
        if not is_paused:
            timer_date = (timer.start_time - timedelta(hours=OFFSET_HOURS)).date()
            reset_time = datetime.combine(timer_date + timedelta(days=1), time(OFFSET_HOURS, 0))
            
            if now >= reset_time:
                if reset_time > timer.start_time + timedelta(minutes=1):
                    try:
                        tb = TimeBlock(task_id=timer.task_id, start_time=timer.start_time, end_time=reset_time)
                        session.add(tb)
                    except Exception as e:
                        print("Error auto-saving timer:", e)
                
                session.delete(timer)
                session.commit()
                return None
        
        return {
            "task_id": timer.task_id, 
            "start_time": timer.start_time.isoformat() if timer.start_time else None,
            "accumulated_seconds": timer.accumulated_seconds,
            "is_paused": is_paused
        }
    return None

@router.post("/pause")
def pause_timer(session: Session = Depends(get_session)):
    timer = session.exec(select(ActiveTimer)).first()
    if timer and timer.start_time:
        now = datetime.now()
        diff = int((now - timer.start_time).total_seconds())
        timer.accumulated_seconds += max(0, diff)
        timer.start_time = None
        session.add(timer)
        session.commit()
    return {"status": "paused"}

@router.post("/resume")
def resume_timer(session: Session = Depends(get_session)):
    timer = session.exec(select(ActiveTimer)).first()
    if timer and timer.start_time is None:
        timer.start_time = datetime.now()
        session.add(timer)
        session.commit()
        return {"status": "resumed", "start_time": timer.start_time.isoformat()}
    return {"status": "ignored"}


@router.delete("/active")
def clear_active_timer(session: Session = Depends(get_session)):
    existing = session.exec(select(ActiveTimer)).all()
    for e in existing:
        session.delete(e)
    session.commit()
    return {"status": "cleared"}
