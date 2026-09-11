from pydantic import BaseModel
from typing import List, Optional


# --- Booking (Abhishek) ---------------------------------------------------

class BookingRequest(BaseModel):
    phone: str
    crop: str
    slot_id: Optional[int] = None


class HaltRequest(BaseModel):
    from_time: str = "00:00"
    reason: str = "Procurement stopped"


# --- Status / Queue (Parv) ------------------------------------------------

class QueueUpdateReq(BaseModel):
    token_number: int
    status: str  # "SERVED" or "NO_SHOW"


class QueueStatusResp(BaseModel):
    token_number: int
    queue_position: int
    estimated_wait_minutes: int
    slot_time: str
    status: str


class QueueItem(BaseModel):
    token_number: int
    name: Optional[str]
    village: Optional[str]
    crop: Optional[str]
    slot_start: str
    slot_end: Optional[str] = None
    status: str


class QueueListResp(BaseModel):
    items: List[QueueItem]
    total_waiting: int
    now_serving: int
