"""Shared FastAPI dependencies: DB session + current user from the session cookie.

Auth model (hackathon-simple, no passwords):
- Google OAuth IS the login. After the callback we set a signed cookie holding
  the user id. itsdangerous signs it with SECRET_KEY so it can't be forged.
- get_current_user reads and verifies that cookie on every request.
"""
from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY
from app.db.models import User
from app.db import repo
from app.db.session import get_session

COOKIE_NAME = "orbi_session"
_signer = URLSafeSerializer(SECRET_KEY, salt="orbi-session")


def make_session_cookie(user_id: int) -> str:
    return _signer.dumps({"user_id": user_id})


def get_current_user(
    orbi_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    session: Session = Depends(get_session),
) -> User:
    if not orbi_session:
        raise HTTPException(status_code=401, detail="Not logged in. Connect Google first.")
    try:
        data = _signer.loads(orbi_session)
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid session cookie.")
    user = repo.get_user(session, data.get("user_id"))
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user.")
    return user
