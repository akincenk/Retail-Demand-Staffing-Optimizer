from datetime import date, timedelta

import pytest

from app.services.forecasting import moving_average
from app.services.staffing import staff_needed

D0 = date(2025, 1, 1)


def series(*units):
    return {D0 + timedelta(days=i): u for i, u in enumerate(units)}


def test_moving_average_uses_last_window_days():
    assert moving_average(series(100, 100, 1, 2, 3), window=3) == 2


def test_moving_average_counts_missing_days_as_zero():
    daily = {D0: 10, D0 + timedelta(days=2): 20}  # Jan 2 had no sales
    assert moving_average(daily, window=3) == 10


def test_moving_average_short_history_uses_available_days():
    assert moving_average(series(4, 8), window=7) == 6


def test_moving_average_requires_history():
    with pytest.raises(ValueError):
        moving_average({}, window=7)


def test_staff_needed_rounds_up_shifts():
    # 1000 units x 0.5 min = 500 min; 8h shift = 480 min -> 2 people
    assert staff_needed(1000, 0.5, 8, min_staff=0, max_staff=20) == 2
    assert staff_needed(960, 0.5, 8, min_staff=0, max_staff=20) == 1


def test_staff_needed_is_clamped():
    assert staff_needed(0, 0.5, 8, min_staff=2, max_staff=20) == 2
    assert staff_needed(100_000, 0.5, 8, min_staff=2, max_staff=12) == 12
