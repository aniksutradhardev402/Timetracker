import os 
from sqlmodel import SQLModel, create_engine , Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:focus_password@db:5432/daily_focus_db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session