"""
Endpoints for the staff dashboard (Pushkar's frontend), at the exact
paths the dashboard expects. These mostly wrap existing logic in
booking.py / admin.py rather than duplicating queries — /slots,
/book-slot, /halt, /resume just re-export those functions under the
paths the frontend calls.

New logic lives here: /dashboard/summary, /queue/live, /alerts,
/analytics.
"""

from fastapi import APIRouter

from .. import schemas
from ..database import get_conn
from ..mandi_state import get_state

from .booking import list_slots, book_slot
from .admin import get_admin_queue, halt_mandi, resume_mandi

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary():
    with get_conn() as conn:
        counts = conn.execute(
            "SELECT status, COUNT(*) FROM bookings "
            "WHERE status IN ('BOOKED', 'SERVED', 'NO_SHOW', 'RESCHEDULED') "
            "GROUP BY status;"
        ).fetchall()
        total_farmers = conn.execute("SELECT COUNT(*) FROM farmers;").fetchone()[0]
        total_slots = conn.execute("SELECT COUNT(*) FROM slots;").fetchone()[0]

    status_counts = {"BOOKED": 0, "SERVED": 0, "NO_SHOW": 0, "RESCHEDULED": 0}
    for status, count in counts:
        status_counts[status] = count

    return {
        "mandi": get_state(),
        "waiting": status_counts["BOOKED"],
        "served": status_counts["SERVED"],
        "no_show": status_counts["NO_SHOW"],
        "rescheduled": status_counts["RESCHEDULED"],
        "total_farmers": total_farmers,
        "total_slots": total_slots,
    }


@router.get("/queue/live")
def queue_live():
    return get_admin_queue()


@router.get("/slots")
def slots():
    return list_slots()


@router.post("/book-slot")
def book_slot_alias(req: schemas.BookingRequest):
    return book_slot(req)


@router.post("/halt")
def halt_alias(req: schemas.HaltRequest):
    return halt_mandi(req)


@router.post("/resume")
def resume_alias():
    return resume_mandi()


@router.get("/alerts")
def alerts():
    """Reschedule alerts for the dashboard's alerts panel — who got
    moved by the last HALT and what message they received."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT n.id, f.name, n.phone, n.channel, n.body, n.status, n.created_at "
            "FROM notifications n JOIN farmers f ON n.farmer_id = f.id "
            "WHERE n.reason = 'RESCHEDULE' "
            "ORDER BY n.id DESC LIMIT 50;"
        ).fetchall()
    return [
        {
            "id": r[0], "name": r[1], "phone": r[2], "channel": r[3],
            "message": r[4], "status": r[5],
            "created_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


@router.get("/analytics")
def analytics():
    with get_conn() as conn:
        by_crop = conn.execute(
            "SELECT crop, COUNT(*) FROM bookings WHERE crop IS NOT NULL "
            "GROUP BY crop ORDER BY COUNT(*) DESC;"
        ).fetchall()
        by_village = conn.execute(
            "SELECT f.village, COUNT(*) FROM bookings b "
            "JOIN farmers f ON b.farmer_id = f.id "
            "WHERE f.village IS NOT NULL "
            "GROUP BY f.village ORDER BY COUNT(*) DESC;"
        ).fetchall()
        by_slot = conn.execute(
            "SELECT s.start_time, COUNT(*) FROM bookings b "
            "JOIN slots s ON b.slot_id = s.id "
            "GROUP BY s.start_time ORDER BY s.start_time;"
        ).fetchall()
        served = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE status = 'SERVED';"
        ).fetchone()[0]
        no_show = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE status = 'NO_SHOW';"
        ).fetchone()[0]
        total_completed = served + no_show

    return {
        "bookings_by_crop": {crop: count for crop, count in by_crop},
        "bookings_by_village": {village: count for village, count in by_village},
        "bookings_by_slot": {str(t): count for t, count in by_slot},
        "served": served,
        "no_show": no_show,
        "no_show_rate": round(no_show / total_completed, 3) if total_completed else None,
    }
