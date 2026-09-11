from fastapi import APIRouter

from .. import schemas
from ..database import get_conn
from ..notifications import queue_message, flush_queue
from .booking import hindi_when

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/tokens")
def get_tokens():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT b.token_number, f.name, f.phone, b.status, "
            "s.slot_date, s.start_time "
            "FROM bookings b "
            "JOIN farmers f ON b.farmer_id = f.id "
            "JOIN slots s ON b.slot_id = s.id "
            "ORDER BY s.slot_date, s.start_time, b.token_number;"
        ).fetchall()
    return [
        {
            "token": r[0], "name": r[1], "phone": r[2], "status": r[3],
            "date": str(r[4]), "time": str(r[5]),
        }
        for r in rows
    ]


@router.get("/queue")
def get_admin_queue():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT b.token_number, f.name, f.village, b.crop, "
            "s.start_time, b.status "
            "FROM bookings b "
            "JOIN farmers f ON b.farmer_id = f.id "
            "JOIN slots s ON b.slot_id = s.id "
            "WHERE b.status IN ('BOOKED', 'SERVED', 'RESCHEDULED') "
            "ORDER BY s.start_time ASC, b.created_at ASC;"
        ).fetchall()
    return [
        {
            "token": r[0], "name": r[1], "village": r[2], "crop": r[3],
            "slot_start": str(r[4]), "status": r[5],
        }
        for r in rows
    ]


@router.post("/halt")
def halt_mandi(req: schemas.HaltRequest):
    moved = []
    with get_conn() as conn:
        affected = conn.execute(
            "SELECT b.id, b.slot_id, b.farmer_id, b.token_number, b.crop, "
            "f.phone, f.name, s.start_time, s.slot_date "
            "FROM bookings b "
            "JOIN slots s ON b.slot_id = s.id "
            "JOIN farmers f ON b.farmer_id = f.id "
            "WHERE s.start_time >= %s AND b.status = 'BOOKED' "
            "ORDER BY b.token_number;",
            (req.from_time,),
        ).fetchall()

        for (bid, old_slot_id, farmer_id, token, crop,
             phone, name, old_time, old_date) in affected:

            conn.execute(
                "UPDATE bookings SET status = 'RESCHEDULED' WHERE id = %s;", (bid,)
            )
            conn.execute(
                "UPDATE slots SET booked = booked - 1 WHERE id = %s;", (old_slot_id,)
            )

            new_slot = conn.execute(
                "SELECT id, slot_date, start_time FROM slots "
                "WHERE slot_date > %s AND booked < capacity "
                "ORDER BY slot_date, start_time LIMIT 1;",
                (old_date,),
            ).fetchone()

            if new_slot:
                new_id, new_date, new_time = new_slot
                conn.execute(
                    "UPDATE slots SET booked = booked + 1 WHERE id = %s;", (new_id,)
                )
                new_token = conn.execute(
                    "SELECT COUNT(*) FROM bookings b JOIN slots s ON b.slot_id = s.id "
                    "WHERE s.slot_date = %s;",
                    (new_date,),
                ).fetchone()[0] + 1
                conn.execute(
                    "INSERT INTO bookings (farmer_id, slot_id, token_number, crop, status) "
                    "VALUES (%s, %s, %s, %s, 'BOOKED');",
                    (farmer_id, new_id, new_token, crop),
                )

                sms_line = (
                    f"MandiQ: Procurement halted at Karnal Mandi. Your new slot is "
                    f"{new_date.strftime('%d %b')} at "
                    f"{new_time.strftime('%I:%M %p').lstrip('0')}. "
                    f"New token {new_token}."
                )
                voice_line = (
                    f"नमस्कार। मंडी में खरीद रुक गई है। आपका नया स्लॉट "
                    f"{hindi_when(new_date, new_time)} का है। "
                    f"आपका नया टोकन नंबर {new_token} है।"
                )
                queue_message(conn, farmer_id, phone, "SMS", sms_line, "RESCHEDULE")
                queue_message(conn, farmer_id, phone, "VOICE", voice_line, "RESCHEDULE")

                moved.append({
                    "name": name, "phone": phone,
                    "old_token": token, "token": new_token,
                    "old_date": str(old_date), "old_time": str(old_time),
                    "new_date": str(new_date), "new_time": str(new_time),
                    "sms": sms_line, "voice_hindi": voice_line,
                })
            else:
                fail_line = "मंडी में खरीद रुक गई है। कृपया दोबारा बुक करें।"
                queue_message(conn, farmer_id, phone, "SMS", fail_line, "RESCHEDULE")
                moved.append({
                    "name": name, "phone": phone, "token": token,
                    "old_date": str(old_date), "old_time": str(old_time),
                    "new_date": None, "new_time": None,
                    "sms": fail_line, "voice_hindi": fail_line,
                })

        conn.commit()

    return {
        "halted": True,
        "reason": req.reason,
        "from_time": req.from_time,
        "affected_count": len(moved),
        "rescheduled": moved,
    }


@router.post("/notifications/flush")
def flush_notifications():
    return flush_queue()


@router.get("/notifications")
def list_notifications():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT n.id, f.name, n.phone, n.channel, n.body, n.reason, "
            "n.status, n.attempts "
            "FROM notifications n JOIN farmers f ON n.farmer_id = f.id "
            "ORDER BY n.id DESC LIMIT 50;"
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "phone": r[2], "channel": r[3],
         "body": r[4], "reason": r[5], "status": r[6], "attempts": r[7]}
        for r in rows
    ]
