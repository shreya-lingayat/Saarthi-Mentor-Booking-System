from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required
from utils.validators import check_mentor_conflict, parse_time

booking_bp = Blueprint("bookings", __name__)


def serialize_time(record):
    if not record:
        return record
    for k, v in list(record.items()):
        if hasattr(v, 'isoformat'):
            record[k] = str(v)
        elif hasattr(v, 'total_seconds'):
            record[k] = parse_time(v)
    return record


@booking_bp.route("", methods=["GET"])
@role_required("admin", "school", "mentor")
def get_bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        user_role = request.user["role"]
        user_id = request.user["user_id"]

        if user_role == "admin":
            cursor.execute("""
                SELECT b.booking_id, b.status, b.created_at,
                       s.organization_name AS school_name,
                       sess.session_id, sess.title AS session_title, sess.session_date, sess.start_time, sess.end_time
                FROM bookings b
                LEFT JOIN schools s ON b.school_id = s.school_id
                LEFT JOIN sessions sess ON b.session_id = sess.session_id
                ORDER BY b.booking_id DESC
            """)
        elif user_role == "school":
            cursor.execute("""
                SELECT b.booking_id, b.status, b.created_at,
                       s.organization_name AS school_name,
                       sess.session_id, sess.title AS session_title, sess.session_date, sess.start_time, sess.end_time
                FROM bookings b
                JOIN schools s ON b.school_id = s.school_id
                LEFT JOIN sessions sess ON b.session_id = sess.session_id
                WHERE s.user_id = %s
                ORDER BY b.booking_id DESC
            """, (user_id,))
        elif user_role == "mentor":
            cursor.execute("""
                SELECT b.booking_id, b.status, b.created_at,
                       s.organization_name AS school_name,
                       sess.session_id, sess.title AS session_title, sess.session_date, sess.start_time, sess.end_time
                FROM bookings b
                LEFT JOIN schools s ON b.school_id = s.school_id
                JOIN sessions sess ON b.session_id = sess.session_id
                JOIN session_mentors sm ON sess.session_id = sm.session_id
                JOIN mentors m ON sm.mentor_id = m.mentor_id
                WHERE m.user_id = %s
                ORDER BY b.booking_id DESC
            """, (user_id,))

        bookings = cursor.fetchall()
        for b in bookings:
            serialize_time(b)
        return jsonify(bookings), 200
    finally:
        cursor.close()
        conn.close()


@booking_bp.route("/<int:booking_id>/status", methods=["PUT"])
@role_required("admin", "mentor")
def update_booking_status(booking_id):
    data = request.get_json() or {}
    status = data.get("status")

    allowed_statuses = ["pending", "approved", "rejected", "cancelled", "completed"]
    if not status or status not in allowed_statuses:
        return jsonify({"error": f"Status must be one of: {', '.join(allowed_statuses)}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # If approving, verify conflict for assigned mentors
        if status == "approved":
            cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (booking["session_id"],))
            session_rec = cursor.fetchone()
            if session_rec:
                cursor.execute(
                    "SELECT mentor_id FROM session_mentors WHERE session_id = %s",
                    (session_rec["session_id"],)
                )
                assigned_mentors = cursor.fetchall()
                for m in assigned_mentors:
                    has_conflict, msg = check_mentor_conflict(
                        conn, m["mentor_id"], session_rec["session_date"], session_rec["start_time"], session_rec["end_time"], exclude_session_id=session_rec["session_id"]
                    )
                    if has_conflict:
                        return jsonify({"error": f"Cannot approve booking due to mentor conflict: {msg}"}), 409

        cursor.execute(
            "UPDATE bookings SET status = %s WHERE booking_id = %s",
            (status, booking_id)
        )
        conn.commit()

        # If booking is completed, also mark session as completed if appropriate
        if status == "completed":
            cursor.execute(
                "UPDATE sessions SET status = 'completed' WHERE session_id = %s",
                (booking["session_id"],)
            )
            conn.commit()

        return jsonify({"message": f"Booking status updated to '{status}'"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
