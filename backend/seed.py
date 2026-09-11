"""
Seed the database from seed_data.csv, against schema.sql (run schema.sql
first). Safe to re-run: skips if farmers already exist.
"""

import csv
from collections import Counter
from datetime import date, datetime

from app.database import get_conn

CAPACITY_BUFFER = 2  # headroom above the seeded count per slot, for live demo bookings


def parse_slot_time(slot_key: str):
    start_str, _end_str = [s.strip() for s in slot_key.split("-")]
    return datetime.strptime(start_str, "%I:%M %p").time()


def seed():
    with open("seed_data.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) FROM farmers;").fetchone()[0]
        if existing:
            print("Database already seeded! Truncate farmers/slots/bookings to reseed.")
            return

        today = date.today()
        slot_counts = Counter(row["slot_time"] for row in rows)

        # Create slots with capacity = seeded count + buffer
        slot_ids = {}
        for slot_key, count in slot_counts.items():
            start_t = parse_slot_time(slot_key)
            row = conn.execute(
                "INSERT INTO slots (slot_date, start_time, capacity, booked) "
                "VALUES (%s, %s, %s, 0) "
                "ON CONFLICT (slot_date, start_time) DO UPDATE SET capacity = EXCLUDED.capacity "
                "RETURNING id;",
                (today, start_t, count + CAPACITY_BUFFER),
            ).fetchone()
            slot_ids[slot_key] = row[0]

        token_counters = Counter()  # per slot_date

        for row in rows:
            farmer = conn.execute(
                "INSERT INTO farmers (phone, name, village) "
                "VALUES (%s, %s, %s) "
                "ON CONFLICT (phone) DO UPDATE SET name = EXCLUDED.name "
                "RETURNING id;",
                (row["phone_number"], row["name"], row["village"]),
            ).fetchone()
            farmer_id = farmer[0]

            slot_id = slot_ids[row["slot_time"]]
            status = row.get("status", "BOOKED").upper()

            token_counters[today] += 1
            token_number = token_counters[today]

            conn.execute(
                "INSERT INTO bookings (farmer_id, slot_id, token_number, crop, status) "
                "VALUES (%s, %s, %s, %s, %s);",
                (farmer_id, slot_id, token_number, row["crop"], status),
            )
            conn.execute(
                "UPDATE slots SET booked = booked + 1 WHERE id = %s;",
                (slot_id,),
            )

        conn.commit()
        print(f"Seeded {len(rows)} farmers/bookings across {len(slot_ids)} slots.")


if __name__ == "__main__":
    seed()
