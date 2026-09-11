from fastapi import APIRouter


router = APIRouter(
    prefix="/farmers",
    tags=["Farmers"]
)


@router.get("/")
def get_farmers():
    return {
        "message": "Farmer list API"
    }


@router.get("/{farmer_id}")
def get_farmer(farmer_id: int):
    return {
        "message": "Farmer details API",
        "farmer_id": farmer_id
    }


@router.post("/register")
def register_farmer():
    return {
        "message": "Farmer registration API"
    }