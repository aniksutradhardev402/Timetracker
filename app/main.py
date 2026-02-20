from contextlib import asynccontextmanager 
from app.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import categories, tasks, callender
from app.routers import analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database Tables...")
    init_db()
    yield


app = FastAPI(title="Daily Focus API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(tasks.router)
app.include_router(callender.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {"status": "Database and API are connected and running!"}
