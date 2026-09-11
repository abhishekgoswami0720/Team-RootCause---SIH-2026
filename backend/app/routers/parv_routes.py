from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from ..database import get_db
from .. import models, schemas

router = APIRouter()

# Assumed constants for wait-time calculation
AVG_PROCESSING_TIME_MINUTES = 5

@router.get("/status/{phone}", response_model=schemas.QueueStatusResp)
async def get_farmer_status(phone: str, db: AsyncSession = Depends(get_db)):
    # Find the farmer
    result = await db.execute(select(models.Farmer).where(models.Farmer.phone_number == phone))
    farmer = result.scalars().first()
    
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    # Get active booking for this farmer
    result = await db.execute(
        select(models.Booking, models.Slot)
        .join(models.Slot)
        .where(models.Booking.farmer_id == farmer.id)
        .where(models.Booking.status.in_([models.BookingStatus.WAITING, models.BookingStatus.RESCHEDULED]))
        .order_by(models.Booking.created_at.desc())
    )
    booking_record = result.first()
    
    if not booking_record:
        raise HTTPException(status_code=404, detail="No active booking found for this farmer")
        
    booking, slot = booking_record
    
    # Calculate queue position: how many people are waiting in the same slot created before this farmer
    pos_result = await db.execute(
        select(func.count(models.Booking.id))
        .where(models.Booking.slot_id == slot.id)
        .where(models.Booking.status == models.BookingStatus.WAITING)
        .where(models.Booking.created_at < booking.created_at)
    )
    queue_position = pos_result.scalar() + 1 # 1-indexed
    
    estimated_wait_minutes = queue_position * AVG_PROCESSING_TIME_MINUTES
    
    # Simple formatting of slot time
    slot_time_str = f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
    
    return schemas.QueueStatusResp(
        token_number=booking.token_number,
        queue_position=queue_position,
        estimated_wait_minutes=estimated_wait_minutes,
        slot_time=slot_time_str,
        status=booking.status
    )

@router.get("/queue", response_model=schemas.QueueListResp)
async def get_full_queue(db: AsyncSession = Depends(get_db)):
    # Get all active tokens for the dashboard
    result = await db.execute(
        select(models.Booking, models.Farmer, models.Slot)
        .join(models.Farmer, models.Booking.farmer_id == models.Farmer.id)
        .join(models.Slot, models.Booking.slot_id == models.Slot.id)
        .where(models.Booking.status.in_([models.BookingStatus.WAITING, models.BookingStatus.SERVED, models.BookingStatus.RESCHEDULED]))
        .order_by(models.Slot.start_time.asc(), models.Booking.created_at.asc())
    )
    
    records = result.all()
    
    items = []
    total_waiting = 0
    now_serving = 0
    
    for booking, farmer, slot in records:
        if booking.status == models.BookingStatus.WAITING.value:
            total_waiting += 1
        elif booking.status == models.BookingStatus.SERVED.value:
            # We can define "now_serving" as the latest served or if we have a specific state for it.
            pass
            
        items.append(schemas.QueueItem(
            token_number=booking.token_number,
            name=farmer.name,
            village=farmer.village,
            crop=farmer.crop,
            slot_start=slot.start_time,
            slot_end=slot.end_time,
            status=booking.status
        ))
        
    return schemas.QueueListResp(
        items=items,
        total_waiting=total_waiting,
        now_serving=now_serving # Might need refinement based on exact definition
    )

@router.post("/queue/update")
async def update_queue_status(req: schemas.QueueUpdateReq, db: AsyncSession = Depends(get_db)):
    if req.status not in [models.BookingStatus.SERVED, models.BookingStatus.NO_SHOW]:
        raise HTTPException(status_code=400, detail="Invalid status update")
        
    result = await db.execute(select(models.Booking).where(models.Booking.token_number == req.token_number))
    booking = result.scalars().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Token not found")
        
    booking.status = req.status
    await db.commit()
    
    return {"message": f"Token {req.token_number} marked as {req.status}"}
