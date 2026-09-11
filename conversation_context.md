# Full Conversation Context & Project Snapshot — v2

**Repo:** `abhishekgoswami0720/Team-RootCause---SIH-2026`
**Branches:** `main` (everything below is merged here), `Priyanshu-voice` (untouched, separate track)
**Last updated:** this session — architecture unification + dashboard endpoints

---

## Project Overview

- **Name:** MandiQ — AI-powered, voice-first slot booking & queue management for agricultural mandis (BookMyShow for mandi slots, over a phone call).
- **Team:** Abhishek (Booking Engine, lead), Parv (Backend Support — this track), Pushkar (Dashboard), Medhavi (Farmer's Phone UI), Priyanshu (Voice), Bhawana (Data/Testing/Pitch).
- **Tech stack (current, as actually shipped — not the original plan):**
  - FastAPI, **raw `psycopg` (sync, v3)** — no ORM.
  - PostgreSQL, with local/cloud failover (`DATABASE_URL` / `LOCAL_DB_URL` / `DB_MODE`).
  - `schema.sql` is the single source of truth for the DB — **not** auto-created by the app on startup. Run `psql -f schema.sql` once against a fresh DB.
  - `app/` package structure: `routers/`, `config/`, `middleware/`, `dependencies/`.
  - Vite/React dashboard (Pushkar) — not present in this repo yet.

> **Note for future-Claude / future-teammate:** an earlier version of this backend used **async SQLAlchemy** (see "History" below). That was fully removed — don't reintroduce it. Everything talks to Postgres via `app/database.py`'s `get_conn()`.

---

## History — what happened since the original handoff

1. **Initial port (branch `parv/backend-support`):** Parv's standalone prototype (async SQLAlchemy: `database.py`, `models.py`, `schemas.py`, `parv_routes.py`, `nlp_matcher.py`, `notifications.py`, `seed.py` + `seed_data.csv`) was merged into the shared `app/` package structure on `medhavi/backend-api`, without touching teammates' existing stub routers (`farmer.py`, `booking.py`, `queue.py`, `voice.py`, `admin.py`).

2. **Architecture collision discovered:** `feature/booking-engine` (Abhishek) had a fully separate, **flat**, **sync-`psycopg`** backend (`backend/main.py`, `db.py`, `notify.py`, `race_test.py`) built directly against `schema.sql`, with a **tested, working double-booking protection** and a working HALT/reschedule flow — completely incompatible with the async-SQLAlchemy prototype. Also found a schema mismatch (`phone` vs `phone_number`, `booked` vs `booked_count`, int vs string `token_number`, etc.).

3. **Resolution (branch `parv/unify-backend-architecture`):** Standardized the whole `app/` package on the **sync-`psycopg` + `schema.sql`** stack (kept, didn't rewrite, the tested booking-engine logic — lower risk than porting concurrency-sensitive code). Rewrote to match:
   - `app/database.py` → `get_conn()` / `active_db()` with local/cloud failover (ported from Abhishek's `db.py`)
   - `app/models.py` → dropped ORM, kept as `BookingStatus` / `NotificationChannel` / `NotificationStatus` string constants
   - `app/schemas.py` → field types now match real columns
   - `app/notifications.py` → merged with `notify.py`
   - `app/routers/parv_routes.py` → `/status/{phone}`, `/queue`, `/queue/update` rewritten as raw SQL
   - `app/routers/booking.py` → real `/bookings/book-slot`, `/bookings/slots`, `/bookings/{id}` (atomic seat protection via `CHECK` constraint + retry-on-conflict)
   - `app/routers/admin.py` → real `/admin/halt`, `/admin/tokens`, `/admin/queue`, notification list/flush
   - `main.py` → dropped `create_all` lifespan; `schema.sql` is applied manually
   - `seed.py`, `race_test.py`, `requirements.txt`, `.env.example` updated/added to match

4. **Merged to `main`:** `parv/unify-backend-architecture` → `medhavi/backend-api` (fast-forward, clean) → PR #1 merged into `main` via GitHub API. **Deleted** the now-superseded branches: `feature/booking-engine`, `medhavi/backend-api`, `parv/backend-support`, `parv/unify-backend-architecture`. Remaining branches: `main`, `Priyanshu-voice`.

5. **Dashboard endpoints added (pushed directly to `main`):** Built `app/routers/dashboard.py` to match Pushkar's exact requested endpoint list — all under `/api/v1/...`, wrapping existing logic rather than duplicating it:
   - `GET /dashboard/summary`, `GET /queue/live`, `GET /slots`, `GET /alerts`, `GET /analytics`, `POST /halt`, `POST /resume`, `POST /book-slot`

6. **Added real halted/active state tracking:** Previously `HALT` rescheduled bookings but never recorded *that* the mandi was halted — so there was nothing for a "resume" to undo. Added:
   - `mandi_state` table (single row, additive — doesn't touch existing tables) in `schema.sql`
   - `migration_mandi_state.sql` for DBs that already ran the old `schema.sql`
   - `app/mandi_state.py` (`get_state()`, `is_active()`, `mark_halted()`, `mark_resumed()`)
   - `halt_mandi()` now calls `mark_halted()`; new `resume_mandi()` calls `mark_resumed()`
   - `book_slot()` now **rejects new bookings while halted**

---

## Current Known Follow-ups (not yet fixed)

| Issue | Detail | Owner needed |
|---|---|---|
| `token_number` not globally unique | Only unique per `slot_date` in `schema.sql`. `/queue/update` matches by token alone — could hit the wrong row if two dates reuse a token number. | Abhishek (schema owner) — needs `UNIQUE(slot_date, token_number)` or switch `/queue/update` to take `booking_id` |
| Dashboard path prefix | New dashboard endpoints are at `/api/v1/...`, but Pushkar's original list omitted the prefix. Needs confirming with him whether his frontend calls the prefixed path. | Pushkar |
| Farmer registration still a stub | `POST /api/v1/farmers/register` (`farmer.py`) is still a placeholder. `book_slot()` requires the farmer to already exist in `farmers` table — so end-to-end booking (new farmer → book) won't work until this is real. | Unassigned — blocks a full demo |
| Voice integration still a stub | `POST /api/v1/voice/inbound` (`voice.py`) just echoes the request body. Sarvam ASR/TTS + `nlp_matcher.py` aren't wired in yet. | Priyanshu (separate `Priyanshu-voice` branch, not yet merged) |
| No dashboard/phone frontend in this repo | Pushkar's React dashboard and Medhavi's phone UI don't appear in any branch here — may live in a separate repo, or just haven't been pushed. | Pushkar / Medhavi |
| `readme.md` / `Project_Context.md` at repo root are stale | Still describe the old SQLAlchemy stack and an outdated status table. Not corrected in this session. | Whoever owns docs |

---

## Current Full API Surface (`/api/v1/...` unless noted)

| Method | Path | Router file | Status |
|---|---|---|---|
| GET | `/` | `main.py` | ✅ real |
| GET | `/health` | `main.py` | ✅ real (reports active DB) |
| GET | `/farmers/` | `farmer.py` | 🚧 stub |
| GET | `/farmers/{farmer_id}` | `farmer.py` | 🚧 stub |
| POST | `/farmers/register` | `farmer.py` | 🚧 stub |
| GET | `/bookings/slots` | `booking.py` | ✅ real |
| POST | `/bookings/book-slot` | `booking.py` | ✅ real — atomic, rejects while halted |
| GET | `/bookings/{booking_id}` | `booking.py` | ✅ real |
| GET | `/bookings/debug/counts` | `booking.py` | ✅ real (dev helper) |
| GET | `/queue/{token_id}` | `queue.py` | 🚧 stub (Pushkar's original stub, unrelated to `/queue` below) |
| POST | `/voice/inbound` | `voice.py` | 🚧 stub |
| GET | `/admin/tokens` | `admin.py` | ✅ real |
| GET | `/admin/queue` | `admin.py` | ✅ real |
| POST | `/admin/halt` | `admin.py` | ✅ real — reschedules + marks mandi halted |
| POST | `/admin/resume` | `admin.py` | ✅ real |
| GET | `/admin/notifications` | `admin.py` | ✅ real |
| POST | `/admin/notifications/flush` | `admin.py` | ✅ real |
| GET | `/status/{phone}` | `parv_routes.py` | ✅ real |
| GET | `/queue` | `parv_routes.py` | ✅ real |
| POST | `/queue/update` | `parv_routes.py` | ✅ real (see token-uniqueness caveat above) |
| GET | `/dashboard/summary` | `dashboard.py` | ✅ real |
| GET | `/queue/live` | `dashboard.py` | ✅ real (wraps `admin.get_admin_queue`) |
| GET | `/slots` | `dashboard.py` | ✅ real (wraps `booking.list_slots`) |
| POST | `/book-slot` | `dashboard.py` | ✅ real (wraps `booking.book_slot`) |
| POST | `/halt` | `dashboard.py` | ✅ real (wraps `admin.halt_mandi`) |
| POST | `/resume` | `dashboard.py` | ✅ real (wraps `admin.resume_mandi`) |
| GET | `/alerts` | `dashboard.py` | ✅ real |
| GET | `/analytics` | `dashboard.py` | ✅ real |

---

## Current `schema.sql` (source of truth)

```sql
CREATE TABLE farmers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100),
    village VARCHAR(100)
);

CREATE TABLE slots (
    id SERIAL PRIMARY KEY,
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    capacity INT NOT NULL DEFAULT 5,
    booked INT NOT NULL DEFAULT 0,
    CONSTRAINT no_overbooking CHECK (booked <= capacity),
    UNIQUE (slot_date, start_time)
);

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    farmer_id INT NOT NULL REFERENCES farmers(id),
    slot_id INT NOT NULL REFERENCES slots(id),
    token_number INT NOT NULL,
    crop VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'BOOKED',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    farmer_id INT NOT NULL REFERENCES farmers(id),
    phone VARCHAR(15) NOT NULL,
    channel VARCHAR(10) NOT NULL,
    body TEXT NOT NULL,
    reason VARCHAR(40) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
    attempts INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP
);

CREATE INDEX idx_bookings_slot ON bookings(slot_id);
CREATE INDEX idx_notif_phone ON notifications(phone);

-- Single-row table tracking whether procurement is currently halted.
CREATE TABLE mandi_state (
    id INT PRIMARY KEY DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    halted_reason VARCHAR(200),
    halted_at TIMESTAMP,
    resumed_at TIMESTAMP,
    CONSTRAINT single_row CHECK (id = 1)
);

INSERT INTO mandi_state (id, active) VALUES (1, TRUE);
```

For a DB that already ran the *old* `schema.sql` (before `mandi_state` existed), run `migration_mandi_state.sql` instead of re-running the whole file.

---

## Full Repo File Tree (tracked files, `main` branch)

```
.gitignore
HACKATHON_PLAN.md
Project_Context.md
readme.md
backend/
│   .env.example
│   .gitignore
│   migration_mandi_state.sql
│   race_test.py
│   requirement.txt
│   requirements.txt
│   run_server.py
│   schema.sql
│   seed.py
│   seed_data.csv
│
└───app/
    │   __init__.py
    │   database.py
    │   main.py
    │   mandi_state.py
    │   models.py
    │   nlp_matcher.py
    │   notifications.py
    │   schemas.py
    │
    ├───config/
    │       settings.py
    │
    ├───dependencies/
    │       common.py
    │
    ├───middleware/
    │       error_handler.py
    │
    └───routers/
            admin.py
            booking.py
            dashboard.py
            farmer.py
            parv_routes.py
            queue.py
            voice.py
```

---

## Environment Setup (for anyone pulling `main` fresh)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL / LOCAL_DB_URL
psql <your-db-url> -f schema.sql   # first time only, on a fresh DB
python run_server.py               # or: uvicorn app.main:app --reload
python seed.py                     # loads seed_data.csv (30 farmers)
python race_test.py                # proves double-booking protection still holds
```

---

## Next Steps (pick one)

1. **Implement real farmer registration** (`POST /farmers/register`) — currently the biggest blocker to an actual end-to-end demo, since `book_slot()` requires a pre-existing farmer row.
2. **Resolve token-uniqueness** with Abhishek — decide between a `UNIQUE(slot_date, token_number)` constraint or switching `/queue/update` to accept `booking_id`.
3. **Confirm the `/api/v1` prefix with Pushkar** and wire the real dashboard frontend against `/dashboard/summary`, `/queue/live`, `/alerts`, `/analytics`, etc.
4. **Merge in `Priyanshu-voice`** once ASR/TTS is ready, and replace the `voice.py` stub with a real `/telephony` webhook that calls `nlp_matcher.parse_farmer_intent()`.
5. **Update `readme.md` / `Project_Context.md`** — both still describe the old SQLAlchemy stack.

---

**How to hand this off to a future Claude session:** point it at this file (`conversation_context.md`, repo root) — no zip needed anymore, everything referenced here is live on `main`.
