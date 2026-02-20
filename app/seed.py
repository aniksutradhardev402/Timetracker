"""
seed.py — 6-month dummy data generator
Starts: Feb 20 2026  |  Ends: Aug 20 2026
7-8 tasks logged per day, mix of streak tasks + rotating random tasks.
No two blocks overlap for the same task on the same day (backend rule respected).
"""
import random
from datetime import datetime, timedelta, date, time as dtime
from sqlmodel import Session, SQLModel
from app.database import engine
from app.models import Category, Task, TimeBlock


# ── Configuration ────────────────────────────────────────────────────
START_DATE = date(2026, 2, 20)
END_DATE   = date(2026, 8, 20)   # ~6 months

# Categories with nice colors
CATEGORIES = [
    ("Deep Work",    "#6366f1"),   # indigo
    ("Fitness",      "#22c55e"),   # green
    ("Learning",     "#f59e0b"),   # amber
    ("Life Admin",   "#3b82f6"),   # blue
    ("Side Project", "#ec4899"),   # pink
    ("Reading",      "#14b8a6"),   # teal
    ("Planning",     "#f97316"),   # orange
]

# Streak tasks — logged EVERY day (simulates strong habits)
STREAK_TASKS = [
    ("Morning Workout",       "Fitness"),
    ("Deep Focus Session",    "Deep Work"),
    ("Read 30 Pages",         "Reading"),
]

# Rotating tasks — picked randomly each day (4-5 per day)
ROTATING_TASKS = [
    ("Write blog post",           "Deep Work"),
    ("Review PRs",                "Deep Work"),
    ("Architecture planning",     "Deep Work"),
    ("Reply to emails",           "Life Admin"),
    ("Pay bills",                 "Life Admin"),
    ("Grocery run",               "Life Admin"),
    ("Doctor appointment",        "Life Admin"),
    ("LeetCode practice",         "Learning"),
    ("Watch lecture",             "Learning"),
    ("Take notes from book",      "Learning"),
    ("Udemy course module",       "Learning"),
    ("Build feature X",           "Side Project"),
    ("Fix bug in side app",       "Side Project"),
    ("Deploy side project",       "Side Project"),
    ("Weekly review",             "Planning"),
    ("Set goals for week",        "Planning"),
    ("Roadmap update",            "Planning"),
    ("Budget review",             "Life Admin"),
    ("Catch up on news",          "Reading"),
    ("Research new tech",         "Learning"),
]

# ── Time slot helpers ────────────────────────────────────────────────

def make_blocks_for_day(tasks_for_day: list, target_date: date) -> list:
    """
    Given a list of task objects, assign non-overlapping time slots
    spread across 06:00–22:00 for that date.
    Returns list of (task_obj, start_dt, end_dt).
    """
    n = len(tasks_for_day)
    total_minutes = 16 * 60   # 06:00 to 22:00 = 960 min
    slot = total_minutes // n

    blocks = []
    cursor = 6 * 60   # start at 06:00 in minutes-from-midnight

    for task in tasks_for_day:
        # Random duration 25–90 min, must not exceed slot
        max_dur = min(90, slot - 10)
        duration = random.randint(25, max(25, max_dur))
        # Random start within the slot (with 5-min buffer)
        jitter = random.randint(0, max(0, slot - duration - 5))
        start_min = cursor + jitter
        end_min   = start_min + duration

        start_dt = datetime.combine(target_date, dtime(start_min // 60, start_min % 60))
        end_dt   = datetime.combine(target_date, dtime(end_min   // 60, end_min   % 60))
        blocks.append((task, start_dt, end_dt))
        cursor += slot

    return blocks


# ── Main seeder ──────────────────────────────────────────────────────

def seed():
    print("⚠️  Purging database...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    print("🌱 Seeding 6 months of dummy data...")

    with Session(engine) as session:

        # 1. Create categories
        cat_map = {}   # name → Category object
        for cat_name, cat_color in CATEGORIES:
            c = Category(name=cat_name, color_hex=cat_color)
            session.add(c)
        session.commit()

        # Reload to get IDs
        for cat_name, _ in CATEGORIES:
            from sqlmodel import select
            cat_obj = session.exec(select(Category).where(Category.name == cat_name)).first()
            cat_map[cat_name] = cat_obj

        # 2. Create streak tasks once — they'll be reused every day
        streak_task_objs = []
        for task_title, cat_name in STREAK_TASKS:
            t = Task(
                title=task_title,
                category_id=cat_map[cat_name].id,
                created_at=datetime.combine(START_DATE, dtime(0, 0))
            )
            session.add(t)
        session.commit()

        from sqlmodel import select
        streak_task_objs = session.exec(
            select(Task).where(Task.title.in_([s[0] for s in STREAK_TASKS]))
        ).all()

        # 3. Create rotating tasks pool
        rotating_task_objs = []
        for task_title, cat_name in ROTATING_TASKS:
            t = Task(
                title=task_title,
                category_id=cat_map[cat_name].id,
                created_at=datetime.combine(START_DATE, dtime(0, 0))
            )
            session.add(t)
        session.commit()

        rotating_task_objs = session.exec(
            select(Task).where(Task.title.in_([r[0] for r in ROTATING_TASKS]))
        ).all()

        # 4. Walk each day and log blocks
        current = START_DATE
        total_days = 0
        total_blocks = 0

        while current <= END_DATE:
            # Pick 4-5 rotating tasks randomly (no repeats)
            daily_rotating = random.sample(rotating_task_objs, k=random.randint(4, 5))

            # Combine streak + rotating (7-8 tasks total)
            daily_tasks = list(streak_task_objs) + daily_rotating
            random.shuffle(daily_tasks)

            blocks = make_blocks_for_day(daily_tasks, current)

            for task_obj, start_dt, end_dt in blocks:
                block = TimeBlock(
                    task_id=task_obj.id,
                    start_time=start_dt,
                    end_time=end_dt
                )
                session.add(block)

            total_blocks += len(blocks)
            total_days += 1
            current += timedelta(days=1)

        session.commit()

    print(f"✅ Done! Seeded {total_days} days × ~{total_blocks // max(total_days,1)} blocks/day = {total_blocks} total time blocks.")


if __name__ == "__main__":
    seed()