import os 
from sqlmodel import SQLModel, create_engine , Session

DATABASE_URL = os.getenv("DATABASE_URL",
"postgresql://postgres:focus_password@db:5432/daily_focus_db")

engine = create_engine("postgresql://postgres:focus_password@db:5432/daily_focus_db", echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session