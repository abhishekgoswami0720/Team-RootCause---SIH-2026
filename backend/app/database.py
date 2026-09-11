"""
Database connection layer.

Single source of truth for how every router talks to Postgres. This
replaces the earlier async-SQLAlchemy prototype: the booking engine's
double-booking protection relies on schema.sql's CHECK constraint plus
plain psycopg transactions, so the whole app now speaks that same
language instead of maintaining two DB access styles side by side.

Supports a CLOUD_URL / LOCAL_URL failover so the app still runs if the
cloud Postgres instance is unreachable during the demo.
"""

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

CLOUD_URL = os.getenv("DATABASE_URL")
LOCAL_URL = os.getenv("LOCAL_DB_URL")
MODE = os.getenv("DB_MODE", "auto").lower()

ACTIVE_URL = None
ACTIVE_NAME = None


def _choose_db():
    global ACTIVE_URL, ACTIVE_NAME
    if MODE == "local":
        ACTIVE_URL, ACTIVE_NAME = LOCAL_URL, "LOCAL (forced)"
    elif MODE == "cloud":
        ACTIVE_URL, ACTIVE_NAME = CLOUD_URL, "CLOUD (forced)"
    else:
        try:
            psycopg.connect(CLOUD_URL, connect_timeout=5).close()
            ACTIVE_URL, ACTIVE_NAME = CLOUD_URL, "CLOUD (auto)"
        except Exception:
            ACTIVE_URL, ACTIVE_NAME = LOCAL_URL, "LOCAL (auto-fallback)"
    print(f"[DB] Using {ACTIVE_NAME}")


_choose_db()


def get_conn():
    return psycopg.connect(ACTIVE_URL)


def active_db():
    return ACTIVE_NAME
