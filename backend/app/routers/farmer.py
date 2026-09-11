import re

import psycopg
from fastapi import APIRouter

from .. import schemas
from ..database import get_conn

router = APIRouter(
    prefix="/farmers",
    tags=["Farmers"]
)

# Matches schema.sql: farmers.phone VARCHAR(15), name/village VARCHAR(100).
# Seed data uses E.164-ish numbers like "+919812012301" (13 chars) — allow an
# optional leading "+" then 7-15 digits so real caller-ID input passes too.
PHONE_RE = re.compile(r"^\+?\d{7,15}$")
MAX_NAME_LEN = 100
MAX_VILLAGE_LEN = 100


def _farmer_dict(row):
    return {"farmer_id": row[0], "phone": row[1], "name": row[2], "village": row[3]}


@router.get("/")
def get_farmers():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, phone, name, village FROM farmers ORDER BY id;"
        ).fetchall()
    return [_farmer_dict(r) for r in rows]


@router.get("/{farmer_id}")
def get_farmer(farmer_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, phone, name, village FROM farmers WHERE id = %s;",
            (farmer_id,),
        ).fetchone()
    if not row:
        return {"success": False, "reason": "Farmer not found"}
    return {"success": True, **_farmer_dict(row)}


@router.post("/register")
def register_farmer(req: schemas.FarmerRegisterRequest):
    phone = req.phone.strip()
    name = req.name.strip() if req.name else None
    village = req.village.strip() if req.village else None

    if not PHONE_RE.match(phone):
        return {
            "success": False,
            "reason": "Phone number must be 7-15 digits, optionally starting with +",
        }
    if name and len(name) > MAX_NAME_LEN:
        return {"success": False, "reason": f"Name too long (max {MAX_NAME_LEN} characters)"}
    if village and len(village) > MAX_VILLAGE_LEN:
        return {"success": False, "reason": f"Village too long (max {MAX_VILLAGE_LEN} characters)"}

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id, name, village FROM farmers WHERE phone = %s;", (phone,)
        ).fetchone()

        if existing:
            farmer_id, existing_name, existing_village = existing
            # Idempotent on purpose: a farmer calling MandiQ again shouldn't
            # hit a hard conflict. Only touch name/village if this call
            # actually supplied them (mirrors seed.py's own
            # ON CONFLICT (phone) DO UPDATE pattern).
            if name or village:
                conn.execute(
                    "UPDATE farmers SET "
                    "name = COALESCE(%s, name), "
                    "village = COALESCE(%s, village) "
                    "WHERE id = %s;",
                    (name, village, farmer_id),
                )
                conn.commit()
                name = name or existing_name
                village = village or existing_village
            else:
                name, village = existing_name, existing_village

            return {
                "success": True,
                "already_registered": True,
                "farmer_id": farmer_id,
                "phone": phone,
                "name": name,
                "village": village,
            }

        try:
            row = conn.execute(
                "INSERT INTO farmers (phone, name, village) "
                "VALUES (%s, %s, %s) RETURNING id;",
                (phone, name, village),
            ).fetchone()
            conn.commit()
        except psycopg.errors.UniqueViolation:
            # Lost a race: another call registered this phone number a
            # moment earlier. Treat it the same as the already-registered
            # branch above rather than surfacing a 500.
            conn.rollback()
            row2 = conn.execute(
                "SELECT id, name, village FROM farmers WHERE phone = %s;", (phone,)
            ).fetchone()
            return {
                "success": True,
                "already_registered": True,
                "farmer_id": row2[0],
                "phone": phone,
                "name": row2[1],
                "village": row2[2],
            }

    return {
        "success": True,
        "already_registered": False,
        "farmer_id": row[0],
        "phone": phone,
        "name": name,
        "village": village,
    }
