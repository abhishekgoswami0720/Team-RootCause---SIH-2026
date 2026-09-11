from fastapi import APIRouter


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


@router.post("/book-slot")
def book_slot():
    return {
        "message": "Book slot API"
    }


@router.get("/{booking_id}")
def get_booking(booking_id: int):
    return {
        "message": "Booking details API",
        "booking_id": booking_id
    }