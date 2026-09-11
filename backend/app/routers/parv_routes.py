from fastapi import APIRouter, HTTPException

from ..database import get_conn
from .. import schemas
from ..models import BookingStatus

router = APIRouter()

AVG_PROCESSING_TIME_MINUTES = 5

# Bookings still "in play" for a farmer / for queue position purposes
ACTIVE_STATUSES = (BookingStatus.BOOKED, BookingStatus.RESCHEDULED)


@router.get("/status/{phone}", response_model=schemas.QueueStatusResp)
def get_farmer_status(phone: str):
    with get_conn() as conn:
        farmer = conn.execute(
            "SELECT id FROM farmers WHERE phone = %s;", (phone,)
        ).fetchone()
        if not farmer:
            raise HTTPException(status_code=404, detail="Farmer not found")
        farmer_id = farmer[0]

        booking_row = conn.execute(
            "SELECT b.id, b.token_number, b.status, b.created_at, "
            "s.id, s.start_time "
            "FROM bookings b JOIN slots s ON b.slot_id = s.id "
            "WHERE b.farmer_id = %s AND b.status = ANY(%s) "
            "ORDER BY b.created_at DESC LIMIT 1;",
            (farmer_id, list(ACTIVE_STATUSES)),
        ).fetchone()
        if not booking_row:
            raise HTTPException(status_code=404, detail="No active booking found for this farmer")

        booking_id, token_number, status, created_at, slot_id, start_time = booking_row

        pos_row = conn.execute(
            "SELECT COUNT(*) FROM bookings "
            "WHERE slot_id = %s AND status = %s AND created_at < %s;",
            (slot_id, BookingStatus.BOOKED, created_at),
        ).fetchone()
        queue_position = pos_row[0] + 1  # 1-indexed

        estimated_wait_minutes = queue_position * AVG_PROCESSING_TIME_MINUTES

        return schemas.QueueStatusResp(
            token_number=token_number,
            queue_position=queue_position,
            estimated_wait_minutes=estimated_wait_minutes,
            slot_time=start_time.strftime("%H:%M"),
            status=status,
        )


@router.get("/queue", response_model=schemas.QueueListResp)
def get_full_queue():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT b.token_number, f.name, f.village, b.crop, "
            "s.start_time, b.status "
            "FROM bookings b "
            "JOIN farmers f ON b.farmer_id = f.id "
            "JOIN slots s ON b.slot_id = s.id "
            "WHERE b.status IN (%s, %s, %s) "
            "ORDER BY s.start_time ASC, b.created_at ASC;",
            (BookingStatus.BOOKED, BookingStatus.SERVED, BookingStatus.RESCHEDULED),
        ).fetchall()

        items = []
        total_waiting = 0
        now_serving = 0

        for token_number, name, village, crop, start_time, status in rows:
            if status == BookingStatus.BOOKED:
                total_waiting += 1
            elif status == BookingStatus.SERVED:
                now_serving += 1

            items.append(schemas.QueueItem(
                token_number=token_number,
                name=name,
                village=village,
                crop=crop,
                slot_start=start_time.strftime("%H:%M"),
                status=status,
            ))

        return schemas.QueueListResp(
            items=items,
            total_waiting=total_waiting,
            now_serving=now_serving,
        )


@router.post("/queue/update")
def update_queue_status(req: schemas.QueueUpdateReq):
    if req.status not in (BookingStatus.SERVED, BookingStatus.NO_SHOW):
        raise HTTPException(status_code=400, detail="Invalid status update")

    with get_conn() as conn:
        booking = conn.execute(
            "SELECT id FROM bookings WHERE token_number = %s AND status = %s;",
            (req.token_number, BookingStatus.BOOKED),
        ).fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Active booking with this token not found")

        conn.execute(
            "UPDATE bookings SET status = %s WHERE id = %s;",
            (req.status, booking[0]),
        )
        conn.commit()

    return {"message": f"Token {req.token_number} marked as {req.status}"}
