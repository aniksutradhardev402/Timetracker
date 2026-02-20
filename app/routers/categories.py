from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Category
from app.schemas import CategoryCreate, CategoryRead


router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=CategoryRead)
async def create_category(
    category: CategoryCreate,
    session: Session = Depends(get_session)
):
    db_category = Category(**category.model_dump())
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategoryRead])
async def read_categories(
    session: Session = Depends(get_session)
):
    categories = session.exec(select(Category)).all()
    return categories

# We use PUT to update an existing category's color or name
@router.put("/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, category: CategoryCreate, session: Session = Depends(get_session)):
    db_category = session.get(Category, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_category.name = category.name
    db_category.color_hex = category.color_hex
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category