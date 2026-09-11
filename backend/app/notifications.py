"""
Notification pipeline.

In production, send_sms() calls a licensed gateway (Gupshup / MSG91) and
send_voice() calls Exotel. Both need DLT registration in India, which
takes weeks, so both are stubbed for the demo. Queueing, status and
retries are real.
"""

from .database import get_conn


def queue_message(conn, farmer_id, phone, channel, body, reason):
    row = conn.execute(
        "INSERT INTO notifications (farmer_id, phone, channel, body, reason) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id;",
        (farmer_id, phone, channel, body, reason),
    ).fetchone()
    return row[0]


def send_sms(phone, body):
    # PRODUCTION: POST to SMS gateway, return provider message id
    return True


def send_voice(phone, body):
    # PRODUCTION: Exotel outbound call, TTS reads `body`
    return True


def flush_queue():
    sent, failed = 0, 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, phone, channel, body FROM notifications "
            "WHERE status IN ('QUEUED','FAILED') AND attempts < 3;"
        ).fetchall()
        for nid, phone, channel, body in rows:
            ok = send_sms(phone, body) if channel == "SMS" else send_voice(phone, body)
            if ok:
                conn.execute(
                    "UPDATE notifications SET status='DELIVERED', "
                    "attempts = attempts + 1, delivered_at = NOW() WHERE id = %s;",
                    (nid,),
                )
                sent += 1
            else:
                conn.execute(
                    "UPDATE notifications SET status='FAILED', "
                    "attempts = attempts + 1 WHERE id = %s;",
                    (nid,),
                )
                failed += 1
        conn.commit()
    return {"sent": sent, "failed": failed}
