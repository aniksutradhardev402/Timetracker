import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session

# Setup a test database in memory
DATABASE_URL = "sqlite://"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Database and API are connected and running!"}

def test_create_category(client: TestClient):
    response = client.post(
        "/categories/",
        json={"name": "Work", "color_hex": "#ff0000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Work"
    assert data["color_hex"] == "#ff0000"
    assert "id" in data

def test_read_categories(client: TestClient):
    client.post("/categories/", json={"name": "Work", "color_hex": "#ff0000"})
    client.post("/categories/", json={"name": "Life", "color_hex": "#00ff00"})
    response = client.get("/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_create_task(client: TestClient):
    # Create category first
    cat_resp = client.post("/categories/", json={"name": "Work", "color_hex": "#ff0000"})
    cat_id = cat_resp.json()["id"]
    
    response = client.post(
        "/tasks/",
        json={"title": "Code", "category_id": cat_id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Code"
    assert data["category_id"] == cat_id

def test_create_time_block(client: TestClient):
    # Setup
    cat_resp = client.post("/categories/", json={"name": "Work", "color_hex": "#ff0000"})
    cat_id = cat_resp.json()["id"]
    task_resp = client.post("/tasks/", json={"title": "Code", "category_id": cat_id})
    task_id = task_resp.json()["id"]
    
    # Create block
    start = "2026-02-20T09:00:00"
    end = "2026-02-20T10:00:00"
    response = client.post(
        "/calendar/block",
        json={"task_id": task_id, "start_time": start, "end_time": end},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id

def test_overlap_constraint(client: TestClient):
    # Setup - two tasks
    cat_resp = client.post("/categories/", json={"name": "Work", "color_hex": "#ff0000"})
    cat_id = cat_resp.json()["id"]
    task1_resp = client.post("/tasks/", json={"title": "Code", "category_id": cat_id})
    task1_id = task1_resp.json()["id"]
    task2_resp = client.post("/tasks/", json={"title": "Meetings", "category_id": cat_id})
    task2_id = task2_resp.json()["id"]
    
    # Create first block for task 1
    client.post(
        "/calendar/block",
        json={"task_id": task1_id, "start_time": "2026-02-20T09:00:00", "end_time": "2026-02-20T10:00:00"},
    )
    
    # Attempt overlapping block for task 2
    response = client.post(
        "/calendar/block",
        json={"task_id": task2_id, "start_time": "2026-02-20T09:30:00", "end_time": "2026-02-20T10:30:00"},
    )
    assert response.status_code == 400
    assert "Overlaps" in response.json()["detail"]

def test_analytics_dashboard(client: TestClient):
    # Setup some data
    cat_resp = client.post("/categories/", json={"name": "Work", "color_hex": "#ff0000"})
    cat_id = cat_resp.json()["id"]
    task_resp = client.post("/tasks/", json={"title": "Code", "category_id": cat_id})
    task_id = task_resp.json()["id"]
    client.post(
        "/calendar/block",
        json={"task_id": task_id, "start_time": "2026-02-20T09:00:00", "end_time": "2026-02-20T10:00:00"},
    )
    
    response = client.get("/analytics/dashboard?start_date=2026-02-20T00:00:00&end_date=2026-02-20T23:59:59")
    assert response.status_code == 200
    data = response.json()
    assert data["total_minutes"] == 60
    assert len(data["pie_chart"]) == 1
    assert data["pie_chart"][0]["name"] == "Work"
