"""
Tracks whether procurement is currently halted, via the single-row
mandi_state table (see schema.sql / migration_mandi_state.sql).
"""

from .database import get_conn


def get_state():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT active, halted_reason, halted_at, resumed_at "
            "FROM mandi_state WHERE id = 1;"
        ).fetchone()
    active, halted_reason, halted_at, resumed_at = row
    return {
        "active": active,
        "halted_reason": halted_reason,
        "halted_at": halted_at.isoformat() if halted_at else None,
        "resumed_at": resumed_at.isoformat() if resumed_at else None,
    }


def is_active() -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT active FROM mandi_state WHERE id = 1;").fetchone()
    return bool(row[0]) if row else True


def mark_halted(conn, reason: str):
    conn.execute(
        "UPDATE mandi_state SET active = FALSE, halted_reason = %s, "
        "halted_at = NOW() WHERE id = 1;",
        (reason,),
    )


def mark_resumed(conn):
    conn.execute(
        "UPDATE mandi_state SET active = TRUE, resumed_at = NOW() WHERE id = 1;"
    )
