"""RSVP to a group event: one answer per (event, user), re-answering replaces,
and RSVPs cascade away with their event (delete-orphan on GroupEvent.rsvps).
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, EventRsvp, User
from app.db import repo

DAY = datetime(2026, 7, 20, tzinfo=timezone.utc)


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _event(session, group, host):
    return repo.create_event(
        session, group_id=group.id, created_by=host.id, kind="event",
        title="Picnic", category="Event", location="Park",
        start_utc=DAY.replace(hour=14), end_utc=DAY.replace(hour=16),
    )


def test_rsvp_upsert_replaces_and_reads_back(session):
    host = User(email="sam@x.com")
    other = User(email="mo@x.com")
    session.add_all([host, other])
    session.commit()
    group = repo.create_group(session, "Crew", host)
    repo.add_member(session, group, other)
    event = _event(session, group, host)

    repo.upsert_rsvp(session, event, host, "going")
    repo.upsert_rsvp(session, event, other, "maybe")
    assert repo.get_event_rsvps(session, event) == {
        "sam@x.com": "going", "mo@x.com": "maybe",
    }

    # answering again replaces, never duplicates
    repo.upsert_rsvp(session, event, other, "cant")
    assert repo.get_event_rsvps(session, event)["mo@x.com"] == "cant"
    assert len(session.scalars(select(EventRsvp)).all()) == 2


def test_rsvps_cascade_away_with_their_event(session):
    host = User(email="sam@x.com")
    session.add(host)
    session.commit()
    group = repo.create_group(session, "Crew", host)
    event = _event(session, group, host)
    repo.upsert_rsvp(session, event, host, "going")

    repo.delete_event(session, event)

    assert session.scalars(select(EventRsvp)).all() == []
