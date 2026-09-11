from fastapi import APIRouter


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/tokens")
def get_tokens():
    return {
        "message": "Admin token monitoring API"
    }


@router.get("/queue")
def get_admin_queue():
    return {
        "message": "Admin queue API"
    }