"""Tests for the interval math in app/tools/slots.py.

Timezone discipline is the #1 bug source in this project, so these tests
deliberately mix UTC, Beirut (UTC+3 in July, has DST) and New York (UTC-4
in July) inputs and assert everything comes back correct in UTC.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.tools.slots import (
    complement,
    find_common_slots,
    intersect,
    merge_intervals,
    reasonable_hours,
)

UTC = timezone.utc
BEIRUT = ZoneInfo("Asia/Beirut")      # UTC+3 in July (EEST)
NEW_YORK = ZoneInfo("America/New_York")  # UTC-4 in July (EDT)


def utc(day: int, hour: int, minute: int = 0) -> datetime:
    """Shorthand: July {day} 2026 at {hour}:{minute} UTC."""
    return datetime(2026, 7, day, hour, minute, tzinfo=UTC)


# ---------------------------------------------------------------- merge

def test_merge_overlapping_and_touching():
    merged = merge_intervals([
        (utc(15, 10), utc(15, 12)),
        (utc(15, 11), utc(15, 13)),   # overlaps previous
        (utc(15, 13), utc(15, 14)),   # touches previous edge
        (utc(15, 16), utc(15, 17)),   # separate
    ])
    assert merged == [(utc(15, 10), utc(15, 14)), (utc(15, 16), utc(15, 17))]


def test_merge_drops_empty_and_inverted_intervals():
    assert merge_intervals([(utc(15, 10), utc(15, 10)), (utc(15, 12), utc(15, 11))]) == []


def test_merge_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="naive"):
        merge_intervals([(datetime(2026, 7, 15, 10), datetime(2026, 7, 15, 11))])


def test_merge_normalizes_mixed_timezones_to_utc():
    # 14:00 Beirut == 11:00 UTC; 07:30 New York == 11:30 UTC -> they overlap
    merged = merge_intervals([
        (datetime(2026, 7, 15, 14, 0, tzinfo=BEIRUT), datetime(2026, 7, 15, 15, 0, tzinfo=BEIRUT)),
        (datetime(2026, 7, 15, 7, 30, tzinfo=NEW_YORK), datetime(2026, 7, 15, 8, 30, tzinfo=NEW_YORK)),
    ])
    assert merged == [(utc(15, 11), utc(15, 12, 30))]


# ---------------------------------------------------------------- complement

def test_complement_basic_gaps():
    busy = [(utc(15, 10), utc(15, 12)), (utc(15, 14), utc(15, 15))]
    free = complement(busy, utc(15, 8), utc(15, 18))
    assert free == [
        (utc(15, 8), utc(15, 10)),
        (utc(15, 12), utc(15, 14)),
        (utc(15, 15), utc(15, 18)),
    ]


def test_complement_busy_spilling_over_window_edges():
    busy = [(utc(14, 23), utc(15, 9)), (utc(15, 17), utc(16, 2))]
    free = complement(busy, utc(15, 8), utc(15, 18))
    assert free == [(utc(15, 9), utc(15, 17))]


def test_complement_fully_busy_means_no_free():
    assert complement([(utc(15, 0), utc(16, 0))], utc(15, 8), utc(15, 18)) == []


def test_complement_no_busy_means_whole_window_free():
    assert complement([], utc(15, 8), utc(15, 18)) == [(utc(15, 8), utc(15, 18))]


# ---------------------------------------------------------------- intersect

def test_intersect_partial_overlaps():
    a = [(utc(15, 9), utc(15, 12)), (utc(15, 14), utc(15, 18))]
    b = [(utc(15, 11), utc(15, 15))]
    assert intersect(a, b) == [(utc(15, 11), utc(15, 12)), (utc(15, 14), utc(15, 15))]


def test_intersect_disjoint_is_empty():
    assert intersect([(utc(15, 9), utc(15, 10))], [(utc(15, 11), utc(15, 12))]) == []


# ---------------------------------------------------------------- reasonable_hours

def test_reasonable_hours_is_local_time_converted_to_utc():
    # Beirut is UTC+3 in July: 09:00-22:00 local == 06:00-19:00 UTC
    allowed = reasonable_hours(utc(15, 0), utc(15, 23, 59), "Asia/Beirut", 9, 22)
    assert (utc(15, 6), utc(15, 19)) in allowed


def test_reasonable_hours_rejects_bad_bounds():
    with pytest.raises(ValueError):
        reasonable_hours(utc(15, 0), utc(16, 0), "Asia/Beirut", 22, 9)


# ---------------------------------------------------------------- find_common_slots

def test_end_to_end_two_members():
    # July 15 2026, Beirut local (UTC+3). Window 06:00-19:00 UTC = 09:00-22:00 local.
    busy = {
        "a@x.com": [(utc(15, 6), utc(15, 9))],    # 09:00-12:00 local
        "b@x.com": [(utc(15, 13), utc(15, 19))],  # 16:00-22:00 local
    }
    slots = find_common_slots(busy, utc(15, 0), utc(15, 23), 60, "Asia/Beirut")
    # only common free window inside reasonable hours: 09:00-13:00 UTC (12:00-16:00 local)
    assert slots == [(utc(15, 9), utc(15, 13))]


def test_no_common_slot_returns_empty():
    busy = {
        "a@x.com": [(utc(15, 6), utc(15, 13))],
        "b@x.com": [(utc(15, 12), utc(15, 19))],
    }
    assert find_common_slots(busy, utc(15, 0), utc(15, 23), 60, "Asia/Beirut") == []


def test_slot_shorter_than_duration_is_dropped():
    busy = {
        "a@x.com": [(utc(15, 6), utc(15, 12)), (utc(15, 12, 45), utc(15, 19))],
    }
    # the 12:00-12:45 UTC gap is only 45 min
    assert find_common_slots(busy, utc(15, 0), utc(15, 23), 60, "Asia/Beirut") == []
    assert find_common_slots(busy, utc(15, 0), utc(15, 23), 30, "Asia/Beirut") == [
        (utc(15, 12), utc(15, 12, 45))
    ]


def test_free_at_3am_is_not_suggested():
    # both members completely free all day -> only the 09:00-22:00 local
    # block may come back, never the middle of the night
    busy = {"a@x.com": [], "b@x.com": []}
    slots = find_common_slots(busy, utc(15, 0), utc(15, 23, 59), 60, "Asia/Beirut")
    assert slots == [(utc(15, 6), utc(15, 19))]  # 09:00-22:00 Beirut


def test_members_in_different_timezones_share_utc_math():
    # a@ is in Beirut, b@ is in New York; their busy blocks arrive in their
    # own local tz. 18:00-20:00 Beirut == 11:00-13:00 New York == 15:00-17:00 UTC:
    # if both are busy then, the result must show the SAME single gap pattern.
    busy = {
        "a@x.com": [(datetime(2026, 7, 15, 18, 0, tzinfo=BEIRUT),
                     datetime(2026, 7, 15, 20, 0, tzinfo=BEIRUT))],
        "b@x.com": [(datetime(2026, 7, 15, 11, 0, tzinfo=NEW_YORK),
                     datetime(2026, 7, 15, 13, 0, tzinfo=NEW_YORK))],
    }
    slots = find_common_slots(busy, utc(15, 0), utc(15, 23, 59), 60, "Asia/Beirut")
    # reasonable hours in Beirut: 06:00-19:00 UTC; both busy 15:00-17:00 UTC
    assert slots == [(utc(15, 6), utc(15, 15)), (utc(15, 17), utc(15, 19))]


def test_multi_day_window():
    busy = {"a@x.com": [(utc(15, 6), utc(15, 19))]}  # all of day 15's local hours
    slots = find_common_slots(busy, utc(15, 0), utc(16, 23, 59), 60, "Asia/Beirut")
    assert slots == [(utc(16, 6), utc(16, 19))]  # day 16 fully open
