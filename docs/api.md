# Orbi REST API

Base URL (dev): `http://localhost:8000` · Interactive docs: `http://localhost:8000/docs`

**Auth model:** Google OAuth *is* the login. After the OAuth callback the server
sets an `orbi_session` cookie (signed, httponly). Every endpoint below except
the two `/auth/google/*` ones requires that cookie — the browser sends it
automatically; with `fetch()` use `credentials: "include"`.

Errors are always `{"detail": "<human-readable message>"}` with an appropriate
status (401 not logged in, 403 not your group, 404 not found, 400 bad input).

---

## Auth

### `GET /auth/google/login`
Redirects (302) to Google's consent screen. Frontend: just
`window.location = "/auth/google/login"`.

### `GET /auth/google/callback`
Google redirects here. Exchanges the code, creates/updates the user, sets the
session cookie, then redirects to `/`. The frontend never calls this directly.

### `GET /auth/me`
Who is logged in.

Response `200`:
```json
{
  "email": "nan0.al.shami2006@gmail.com",
  "timezone": "Asia/Beirut",
  "calendar_connected": true
}
```
Response `401`: `{"detail": "Not logged in. Connect Google first."}`

### `POST /auth/logout`
Clears the cookie. Response `200`: `{"ok": true}`

---

## Groups

### `POST /groups`
Create a group; the creator is automatically the first member.

Request:
```json
{"name": "Beirut Crew"}
```
Response `200`:
```json
{"id": 1, "name": "Beirut Crew", "invite_code": "4PYJU8"}
```

### `POST /groups/join`
Join by invite code (idempotent — joining twice is fine).

Request:
```json
{"invite_code": "4PYJU8"}
```
Response `200`:
```json
{"id": 1, "name": "Beirut Crew", "invite_code": "4PYJU8"}
```
Response `404`: `{"detail": "No group with that invite code."}`

### `GET /groups`
Groups the current user belongs to.

Response `200`:
```json
[{"id": 1, "name": "Beirut Crew", "invite_code": "4PYJU8"}]
```

### `GET /groups/{group_id}/members`
Response `200`:
```json
[
  {"email": "nan0.al.shami2006@gmail.com", "calendar_connected": true},
  {"email": "nano.06dev@gmail.com", "calendar_connected": true}
]
```
Response `403`: `{"detail": "You are not in this group."}`

---

## Chat (the Orbi orb)

### `POST /chat`
One turn of the agent. **Stateless**: the frontend keeps the conversation and
sends it back as `history` each time (max 40 items). `group_id` may be null if
the user has no group yet — Orbi will tell them to create/join one.

Request:
```json
{
  "group_id": 1,
  "message": "Find a time this week when everyone's free",
  "history": [
    {"role": "user", "content": "hey orbi"},
    {"role": "assistant", "content": "Hi! I can help your group find a time to meet."}
  ]
}
```

Response `200`:
```json
{
  "reply": "Everyone is free Thursday 17 July between 18:00 and 22:00 — it's the only evening this week with no conflicts for both of you. Want me to look at other days?",
  "trace": [
    {"kind": "tool_call",   "name": "get_group_members",  "detail": {}},
    {"kind": "tool_result", "name": "get_group_members",  "detail": {"group_name": "Beirut Crew", "member_count": 2, "members": [...]}},
    {"kind": "tool_call",   "name": "find_meeting_slots", "detail": {"days_ahead": 7, "duration_minutes": 60}},
    {"kind": "tool_result", "name": "find_meeting_slots", "detail": {"common_slots": [...], "...": "..."}},
    {"kind": "text",        "name": "",                   "detail": "Everyone is free Thursday..."}
  ]
}
```

`trace` is the agent's visible reasoning loop — render it as collapsible
"Orbi is checking calendars…" steps if you want the agentic feel in the UI.
All times inside `reply` are already in the user's local timezone.

Notes for the UI:
- The call can take several seconds (live Google Calendar queries + the model).
  Show a thinking state on the orb.
- Each call uses Groq free-tier quota — don't auto-fire it; only send on user action.

---

## Polls & voting

Polls are **created by Orbi** (via chat — there is no create-poll REST endpoint);
members then vote through these endpoints. The decision rule runs after every
vote: any NO ⇒ `rejected`; zero NO and ≥ `min_yes` YES ⇒ `approved`; else stays
`open`. Booking happens through Orbi too, and only for approved polls.

### `GET /groups/{group_id}/polls`
Newest first, max 10.

Response `200`:
```json
[
  {
    "id": 3,
    "title": "Coffee catch-up",
    "location": "Kalei Coffee, Mar Mikhael",
    "start_local": "Thu 16 Jul 19:00",
    "end_local": "Thu 16 Jul 20:00",
    "status": "open",
    "booked": false,
    "event_link": null,
    "yes": 1,
    "no": 0,
    "min_yes": 2,
    "waiting_on": ["nano.06dev@gmail.com"]
  }
]
```
`status`: `open` | `approved` | `rejected`. Once booked, `booked: true` and
`event_link` is the Google Calendar link.

### `POST /polls/{poll_id}/vote`
Voting again replaces your previous vote. Closed/booked polls reject votes.

Request:
```json
{"yes": true}
```
Response `200`: the updated poll object (same shape as above).
Response `400`: `{"detail": "Poll is rejected; voting is closed."}`
Response `403`: `{"detail": "You are not in this group."}`
