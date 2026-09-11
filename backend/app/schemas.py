from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time, datetime

class QueueUpdateReq(BaseModel):
    token_number: str
    status: str # "served" or "no_show"

class QueueStatusResp(BaseModel):
    token_number: str
    queue_position: int
    estimated_wait_minutes: int
    slot_time: str
    status: str

class QueueItem(BaseModel):
    token_number: str
    name: Optional[str]
    village: Optional[str]
    crop: Optional[str]
    slot_start: time
    slot_end: time
    status: str

class QueueListResp(BaseModel):
    items: List[QueueItem]
    total_waiting: int
    now_serving: int
