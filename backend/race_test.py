"""
Two farmers, one seat, same millisecond.
Proves the database prevents double-booking, not lucky timing.

Run against a live server: uvicorn app.main:app --reload
"""

import asyncio
import httpx

API = "http://127.0.0.1:8000/api/v1/bookings"


async def get_contested_slot(client):
    """Find the slot with exactly one seat left."""
    r = await client.get(f"{API}/slots")
    for s in r.json():
        if s["seats_left"] == 1:
            return s
    return None


async def book(client, phone, label, slot_id):
    r = await client.post(f"{API}/book-slot", json={
        "phone": phone, "crop": "Wheat", "slot_id": slot_id,
    })
    return label, r.json()


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        slot = await get_contested_slot(client)
        if not slot:
            print("No slot with exactly 1 seat left. Run seed.py first.")
            return

        print(f"\nContested slot: {slot['time'][:5]} on {slot['date']} "
              f"({slot['seats_left']} seat left)")
        print("Two farmers requesting it at the same moment...\n")

        results = await asyncio.gather(
            book(client, "9876500003", "Mahesh", slot["slot_id"]),
            book(client, "9876500004", "Jagdish", slot["slot_id"]),
        )

        print("=" * 58)
        for label, d in results:
            if d.get("success"):
                won = d.get("got_requested_slot")
                verdict = "WON the contested seat" if won else "slot full -> auto-moved"
                print(f"\n{label:10} {verdict}")
                print(f"{'':10} time  : {d['time'][:5]} on {d['date']}")
                print(f"{'':10} token : {d['token']}")
            else:
                print(f"\n{label:10} no booking - {d.get('reason')}")
        print("\n" + "=" * 58)

        r = await client.get(f"{API}/slots")
        after = next(s for s in r.json() if s["slot_id"] == slot["slot_id"])
        print(f"\nSlot now: booked {after['booked']} / capacity {after['capacity']}")
        if after["booked"] <= after["capacity"]:
            print("PASS - capacity never exceeded")
        else:
            print("FAIL - overbooked")

asyncio.run(main())
