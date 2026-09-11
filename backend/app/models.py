"""
Shared constants for the booking lifecycle.

No ORM layer — every router talks to schema.sql directly via
app.database.get_conn(). This file just centralizes the status
strings so "BOOKED" / "SERVED" etc. aren't typo'd differently across
routers.
"""


class BookingStatus:
    BOOKED = "BOOKED"
    SERVED = "SERVED"
    NO_SHOW = "NO_SHOW"
    RESCHEDULED = "RESCHEDULED"


class NotificationChannel:
    SMS = "SMS"
    VOICE = "VOICE"


class NotificationStatus:
    QUEUED = "QUEUED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
