"""
test_streak.py — Unit tests for the streak calculation logic.

Run with:  pytest tests/test_streak.py -v

Tests the core streak algorithm in isolation (no DB needed).
"""
from datetime import date, timedelta


def compute_streak(unique_dates_past: list[date], today: date) -> int:
    """
    Replica of the streak logic from analytics.py.
    unique_dates_past: list of dates <= today, sorted descending.
    """
    if not unique_dates_past:
        return 0
    if unique_dates_past[0] not in (today, today - timedelta(days=1)):
        return 0

    streak = 1
    current = unique_dates_past[0]
    for d in unique_dates_past[1:]:
        if d == current - timedelta(days=1):
            streak += 1
            current = d
        else:
            break
    return streak


TODAY = date(2026, 2, 20)


# ── Happy-path tests ─────────────────────────────────────────────────

def test_streak_of_one_logged_today():
    dates = [TODAY]
    assert compute_streak(dates, TODAY) == 1


def test_streak_of_one_logged_yesterday():
    dates = [TODAY - timedelta(days=1)]
    assert compute_streak(dates, TODAY) == 1


def test_streak_of_five_consecutive():
    dates = [TODAY - timedelta(days=i) for i in range(5)]
    assert compute_streak(dates, TODAY) == 5


def test_streak_broken_by_gap():
    # logged today + 3 days ago → streak = 1 (gap on day 2)
    dates = [TODAY, TODAY - timedelta(days=3)]
    assert compute_streak(dates, TODAY) == 1


def test_streak_broken_after_two():
    dates = [TODAY, TODAY - timedelta(days=1), TODAY - timedelta(days=3)]
    assert compute_streak(dates, TODAY) == 2


def test_no_dates():
    assert compute_streak([], TODAY) == 0


def test_only_future_dates_ignored():
    # Should already be filtered by backend, but streak = 0 if none <= today
    assert compute_streak([], TODAY) == 0


def test_streak_oldest_day_in_range():
    # 7 days in a row, ending yesterday — still counts
    dates = [TODAY - timedelta(days=i) for i in range(1, 8)]
    assert compute_streak(dates, TODAY) == 7


def test_streak_with_extra_old_dates():
    # 3-day streak then a big gap then more old data
    dates = (
        [TODAY - timedelta(days=i) for i in range(3)]
        + [TODAY - timedelta(days=10), TODAY - timedelta(days=11)]
    )
    assert compute_streak(dates, TODAY) == 3


def test_streak_missed_by_two_days():
    # Last logged 2 days ago → streak = 0 (must be today or yesterday)
    dates = [TODAY - timedelta(days=2)]
    assert compute_streak(dates, TODAY) == 0


def test_large_6_month_streak():
    dates = [TODAY - timedelta(days=i) for i in range(182)]
    assert compute_streak(dates, TODAY) == 182


if __name__ == "__main__":
    tests = [
        test_streak_of_one_logged_today,
        test_streak_of_one_logged_yesterday,
        test_streak_of_five_consecutive,
        test_streak_broken_by_gap,
        test_streak_broken_after_two,
        test_no_dates,
        test_only_future_dates_ignored,
        test_streak_oldest_day_in_range,
        test_streak_with_extra_old_dates,
        test_streak_missed_by_two_days,
        test_large_6_month_streak,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAIL  {t.__name__}  →  {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} tests passed")
