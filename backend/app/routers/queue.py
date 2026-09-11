from fastapi import APIRouter


router = APIRouter(
    prefix="/queue",
    tags=["Queue"]
)


@router.get("/{token_id}")
def get_queue(token_id: str):
    return {
        "message": "Queue status API",
        "token_id": token_id
    }