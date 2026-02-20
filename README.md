#  Daily Focus Time Tracker

Daily Focus is a professional, full-stack time tracking application designed to help you organize your day, track habits, and visualize your productivity. 

Built with a high-performance **FastAPI** backend and a sleek **Streamlit** frontend, it leverages a robust **PostgreSQL** database to manage your tasks and time blocks with precision.

---
## ScreenShots


![Dashboard](assets/dashboard.png)
![Tasks](assets/tasks.png)
![Analytics](assets/analytics.png)
![Categories](assets/categories.png)


##  Features

- **Task Management**: Create, update, and organize tasks with specific categories.
- **Time Blocking**: Log precise time intervals for each task, ensuring no overlapping slots.
- **Category Organization**: Group your work into vibrant, color-coded categories (Deep Work, Fitness, Learning, etc.).
- **Analytics Dashboard**: Visualize your progress with intuitive charts and statistics.
- **Habit Tracking**: Maintain streaks for your core daily routines.

---

## Tech Stack

- **Backend**: Python 3.11, [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic).
- **Frontend**: [Streamlit](https://streamlit.io/).
- **Database**: [PostgreSQL](https://www.postgresql.org/) 15.
- **Containerization**: [Docker](https://www.docker.com/), Docker Compose.

---

## Getting Started (Docker)

The easiest way to get the application running is using Docker Compose.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- [Docker Compose](https://docs.docker.com/compose/install/) (standard with Docker Desktop).

### ⚙️ Installation & Setup

1. **Clone the Repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd daily_focus_backend
   ```

2. **Start the Application**:
   Run the following command to build and launch all services (Frontend, Backend, and Database):
   ```bash
   docker-compose up --build
   ```

3. **Access the Application**:
   - **Frontend UI**: [http://localhost:8501](http://localhost:8501)
   - **Backend API (Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Seeding the Database

To quickly populate the application with 6 months of demo data for testing and visualization:

```bash
docker exec daily_focus_backend python -m app.seed
```

This will purge the existing database and generate approximately 1,300+ time blocks across categories like "Deep Work", "Learning", and "Fitness".

---

## Project Structure

```text
.
├── app/                # FastAPI Backend Application
│   ├── models.py       # SQLModel database schemas
│   ├── routers/        # API endpoints (tasks, analytics, categories)
│   ├── seed.py         # Dummy data generator
│   └── main.py         # Application entry point
├── frontend/           # Streamlit Frontend Application
│   └── frontend.py     # Main UI logic
├── docker-compose.yml  # Docker orchestration configuration
└── Dockerfile          # Backend container definition
```

---

