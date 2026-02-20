from sqlmodel import Session, select, delete
from app.database import engine
from app.models import Category, Task, TimeBlock

def clean_database():
    print("Clearing all data from the database...")
    with Session(engine) as session:
        # Delete in order of dependencies
        session.execute(delete(TimeBlock))
        session.execute(delete(Task))
        session.execute(delete(Category))
        session.commit()
    print("Database cleared successfully!")

if __name__ == "__main__":
    clean_database()
