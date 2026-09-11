from fastapi import APIRouter, Request


router = APIRouter(
    prefix="/voice",
    tags=["Voice"]
)


@router.post("/inbound")
async def voice_inbound(request: Request):
    data = await request.json()

    return {
        "message": "Voice request received",
        "data": data
    }