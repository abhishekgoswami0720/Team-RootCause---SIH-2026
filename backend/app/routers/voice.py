"""
Voice inbound endpoint — Hindi transcript in, a real booking result out.

Flow: transcript -> deterministic NLU (village + crop; zero LLM, zero
guessing, see voice/README.md's architectural rule) -> if and only if
both fields resolve unambiguously, register/update the farmer's village
and call the real booking engine -> return exactly what
/bookings/book-slot would return (plus the extracted village/crop).

If the NLU can't confidently resolve both fields, NO booking is
attempted. We return the missing/ambiguous fields and a Hindi prompt so
the caller can be asked again — the phone-simulator falls back to the
keypad in that case, which always works.

This router is deliberately thin: it never re-implements farmer
registration or booking logic, it just calls the existing functions.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .. import schemas
from .booking import book_slot
from .farmer import register_farmer

from voice.nlu import DeterministicNLU

router = APIRouter(
    prefix="/voice",
    tags=["Voice"]
)

_nlu = DeterministicNLU()

_MISSING_PROMPTS = {
    "village": "आपका गाँव समझ नहीं आया। कृपया कीपैड से चुनें।",
    "crop": "आपकी फसल समझ नहीं आई। कृपया कीपैड से चुनें।",
}


class VoiceInboundRequest(BaseModel):
    phone: str
    transcript: str
    timestamp: Optional[str] = None


def _prompt_for(unresolved_fields: List[str]) -> str:
    # Ask about whichever field is missing/ambiguous; lead with village if both are.
    for field in ("village", "crop"):
        if field in unresolved_fields:
            return _MISSING_PROMPTS[field]
    return "माफ़ कीजिए, आपकी बात समझ नहीं आई। कृपया कीपैड का उपयोग करें।"


@router.post("/inbound")
def voice_inbound(req: VoiceInboundRequest):
    result = _nlu.parse(req.transcript)

    if not result["success"]:
        unresolved = result["missing_fields"] or result["ambiguous_fields"]
        return {
            "success": False,
            "village": result["village"],
            "crop": result["crop"],
            "missing_fields": result["missing_fields"],
            "ambiguous_fields": result["ambiguous_fields"],
            "prompt_hindi": _prompt_for(unresolved),
        }

    village = result["village"]
    crop = result["crop"]

    # Make sure the farmer exists before handing off to the booking engine
    # (book_slot deliberately rejects unregistered phone numbers) — same
    # thing the phone-simulator's keypad path already does client-side.
    register_farmer(schemas.FarmerRegisterRequest(phone=req.phone, village=village))

    booking_result = book_slot(schemas.BookingRequest(phone=req.phone, crop=crop))

    return {
        **booking_result,
        "village": village,
        "crop": crop,
    }
