"""Chat endpoint: one turn of the Orbi agent.

POST /chat  {"group_id": 1, "message": "...", "history": [...]}
  -> {"reply": "...", "trace": [...]}

Stateless by design: the frontend holds the conversation history and sends it
back each turn (simplest thing that works; the API itself stays sessionless).
`trace` lists every tool call the agent made this turn so the UI can render
the reasoning steps.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent.loop import run_agent
from app.agent.tools import ToolContext
from app.api.deps import get_current_user
from app.db.models import User
from app.db import repo
from app.db.session import get_session

router = APIRouter(tags=["chat"])


class HistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatBody(BaseModel):
    group_id: int | None = None
    message: str = Field(min_length=1, max_length=2000)
    history: list[HistoryItem] = Field(default_factory=list, max_length=40)


@router.post("/chat")
def chat(
    body: ChatBody,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    group = None
    if body.group_id is not None:
        my_groups = {g.id: g for g in repo.get_user_groups(session, user)}
        group = my_groups.get(body.group_id)
        if group is None:
            raise HTTPException(status_code=403, detail="You are not in this group.")

    ctx = ToolContext(
        session=session,
        user=user,
        group=group,
        now_utc=datetime.now(timezone.utc),  # fresh "now" injected every turn
        tz_name=user.timezone,
    )
    result = run_agent(
        ctx,
        history=[h.model_dump() for h in body.history],
        user_message=body.message,
    )
    return {"reply": result.reply, "trace": [asdict(s) for s in result.trace]}
