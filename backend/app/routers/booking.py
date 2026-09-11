from datetime import date as _date, datetime as _dt

import psycopg
from fastapi import APIRouter

from .. import schemas
from ..database import get_conn, active_db
from ..mandi_state import is_active

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

HOUR_HI = {9: "नौ", 10: "दस", 11: "ग्यारह", 12: "बारह", 1: "एक", 2: "दो", 3: "तीन"}
MIN_HI = {15: "पंद्रह", 30: "तीस", 45: "पैंतालीस"}
WEEKDAY_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


def hindi_when(slot_date, start_time):
    """Turn a date + time into natural spoken Hindi."""
    diff = (slot_date - _date.today()).days
    weekday = WEEKDAY_HI[slot_date.weekday()]
    if diff == 0:
        day = "आज"
    elif diff == 1:
        day = f"कल {weekday}"
    elif diff == 2:
        day = f"परसों {weekday}"
    else:
        day = f"{weekday}, {slot_date.day} तारीख"

    h, m = start_time.hour, start_time.minute
    part = "सुबह" if h < 12 else "दोपहर"
    hh = HOUR_HI.get(h if h <= 12 else h - 12, str(h))
    clock = f"{hh} बजे" if m == 0 else f"{hh} बजकर {MIN_HI.get(m, str(m))} मिनट"
    return f"{day} {part} {clock}"


@router.get("/slots")
def list_slots():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, slot_date, start_time, capacity, booked "
            "FROM slots ORDER BY slot_date, start_time;"
        ).fetchall()
    return [
        {
            "slot_id": r[0],
            "date": str(r[1]),
            "time": str(r[2]),
            "capacity": r[3],
            "booked": r[4],
            "seats_left": r[3] - r[4],
        }
        for r in rows
    ]


@router.post("/book-slot")
def book_slot(req: schemas.BookingRequest):
    if not is_active():
        return {"success": False, "reason": "Procurement is currently halted"}

    with get_conn() as conn:
        farmer = conn.execute(
            "SELECT id FROM farmers WHERE phone = %s;", (req.phone,)
        ).fetchone()
        if not farmer:
            return {"success": False, "reason": "Farmer not registered"}
        farmer_id = farmer[0]

        # one active booking per farmer — a second call reads back his slot
        existing = conn.execute(
            "SELECT b.token_number, s.slot_date, s.start_time "
            "FROM bookings b JOIN slots s ON b.slot_id = s.id "
            "WHERE b.farmer_id = %s AND b.status = 'BOOKED' "
            "ORDER BY s.slot_date, s.start_time LIMIT 1;",
            (farmer_id,),
        ).fetchone()
        if existing:
            e_token, e_date, e_time = existing
            return {
                "success": False,
                "reason": "Already booked",
                "token": e_token,
                "date": str(e_date),
                "time": str(e_time),
                "message_hindi": (
                    f"आपकी बुकिंग पहले से है। आपका स्लॉट "
                    f"{hindi_when(e_date, e_time)} का है। "
                    f"आपका टोकन नंबर {e_token} है।"
                ),
            }

        # never offer a slot that has already passed
        now = _dt.now()
        slots = conn.execute(
            "SELECT id, slot_date, start_time FROM slots "
            "WHERE booked < capacity "
            "AND (slot_date > %s OR (slot_date = %s AND start_time > %s)) "
            "ORDER BY slot_date, start_time;",
            (now.date(), now.date(), now.time()),
        ).fetchall()

        requested_slot = req.slot_id
        if requested_slot:
            slots.sort(key=lambda s: 0 if s[0] == requested_slot else 1)

        for slot_id, slot_date, start_time in slots:
            try:
                conn.execute(
                    "UPDATE slots SET booked = booked + 1 WHERE id = %s;", (slot_id,)
                )
                count = conn.execute(
                    "SELECT COUNT(*) FROM bookings b JOIN slots s ON b.slot_id = s.id "
                    "WHERE s.slot_date = %s;",
                    (slot_date,),
                ).fetchone()[0]
                token = count + 1
                conn.execute(
                    "INSERT INTO bookings (farmer_id, slot_id, token_number, crop) "
                    "VALUES (%s, %s, %s, %s);",
                    (farmer_id, slot_id, token, req.crop),
                )
                conn.commit()
                return {
                    "success": True,
                    "slot_id": slot_id,
                    "date": str(slot_date),
                    "time": str(start_time),
                    "token": token,
                    "got_requested_slot": (slot_id == requested_slot) if requested_slot else None,
                    "message_hindi": (
                        f"आपको {hindi_when(slot_date, start_time)} का स्लॉट मिला है। "
                        f"आपका टोकन नंबर {token} है।"
                    ),
                }
            except psycopg.errors.CheckViolation:
                # someone took the last seat a millisecond earlier — try the next slot
                conn.rollback()
                continue

    return {"success": False, "reason": "No slots available"}


@router.get("/{booking_id}")
def get_booking(booking_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT b.id, b.token_number, b.status, b.crop, "
            "f.name, f.phone, s.slot_date, s.start_time "
            "FROM bookings b "
            "JOIN farmers f ON b.farmer_id = f.id "
            "JOIN slots s ON b.slot_id = s.id "
            "WHERE b.id = %s;",
            (booking_id,),
        ).fetchone()
    if not row:
        return {"message": "Booking not found"}
    bid, token, status, crop, name, phone, slot_date, start_time = row
    return {
        "booking_id": bid,
        "token": token,
        "status": status,
        "crop": crop,
        "name": name,
        "phone": phone,
        "date": str(slot_date),
        "time": str(start_time),
    }


@router.get("/debug/counts")
def debug():
    with get_conn() as conn:
        farmers = conn.execute("SELECT COUNT(*) FROM farmers;").fetchone()[0]
        slots = conn.execute("SELECT COUNT(*) FROM slots;").fetchone()[0]
        bookings = conn.execute("SELECT COUNT(*) FROM bookings;").fetchone()[0]
    return {
        "database": active_db(),
        "farmers": farmers,
        "slots": slots,
        "bookings": bookings,
    }
