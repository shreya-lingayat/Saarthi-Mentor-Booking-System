from flask import Blueprint, jsonify

from db import get_db_connection
from utils.decorators import role_required
from utils.validators import parse_time

feedback_bp = Blueprint("feedback", __name__)


def serialize_time(record):
    if not record:
        return record
    for k, v in list(record.items()):
        if hasattr(v, 'isoformat'):
            record[k] = str(v)
        elif hasattr(v, 'total_seconds'):
            record[k] = parse_time(v)
    return record


@feedback_bp.route("", methods=["GET"])
@role_required("admin", "school", "mentor")
def get_all_feedback():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT f.feedback_id, f.booking_id, f.rating, f.comments, f.created_at,
                   s.organization_name AS school_name,
                   sess.title AS session_title
            FROM feedback f
            JOIN bookings b ON f.booking_id = b.booking_id
            LEFT JOIN schools s ON b.school_id = s.school_id
            LEFT JOIN sessions sess ON b.session_id = sess.session_id
            ORDER BY f.feedback_id DESC
        """
        cursor.execute(query)
        feedbacks = cursor.fetchall()
        for f in feedbacks:
            serialize_time(f)
        return jsonify(feedbacks), 200
    finally:
        cursor.close()
        conn.close()
