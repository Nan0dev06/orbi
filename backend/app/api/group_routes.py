"""Group endpoints: create with invite code, join by code, list mine.

POST /groups            {"name": "Beirut Crew"}         -> group + invite_code
POST /groups/join       {"invite_code": "4PYJU8"}       -> joined group
GET  /groups            -> groups the current user belongs to
GET  /groups/{id}/members -> members + calendar connection status
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Group, User
from app.db import repo
from app.db.session import get_session

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupBody(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class JoinGroupBody(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6)


def _group_json(group: Group) -> dict:
    return {"id": group.id, "name": group.name, "invite_code": group.invite_code}


@router.post("")
def create_group(
    body: CreateGroupBody,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group = repo.create_group(session, body.name, user)
    return _group_json(group)


@router.post("/join")
def join_group(
    body: JoinGroupBody,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group = repo.get_group_by_code(session, body.invite_code)
    if group is None:
        raise HTTPException(status_code=404, detail="No group with that invite code.")
    repo.add_member(session, group, user)
    return _group_json(group)


@router.get("")
def my_groups(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return [_group_json(g) for g in repo.get_user_groups(session, user)]


@router.get("/{group_id}/members")
def group_members(
    group_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    groups = {g.id for g in repo.get_user_groups(session, user)}
    if group_id not in groups:
        raise HTTPException(status_code=403, detail="You are not in this group.")
    members = repo.get_group_members(session, group_id)
    return [
        {"email": m.email, "calendar_connected": m.calendar_connected}
        for m in members
    ]
