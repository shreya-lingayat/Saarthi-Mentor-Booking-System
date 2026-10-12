from flask import Blueprint, jsonify

from db import get_db_connection
from utils.decorators import role_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@role_required("admin", "school", "mentor")
def get_dashboard_analytics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total_users = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM mentors")
        total_mentors = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM schools")
        total_schools = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM sessions")
        total_sessions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM sessions WHERE status = 'completed'")
        completed_sessions = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM bookings WHERE status = 'pending'")
        pending_bookings = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT s.organization_name, COUNT(b.booking_id) AS booking_count
            FROM schools s
            LEFT JOIN bookings b ON s.school_id = b.school_id
            GROUP BY s.school_id, s.organization_name
            ORDER BY booking_count DESC
        """)
        bookings_by_school = cursor.fetchall()

        cursor.execute("""
            SELECT m.name AS mentor_name, COUNT(sm.session_id) AS session_count
            FROM mentors m
            LEFT JOIN session_mentors sm ON m.mentor_id = sm.mentor_id
            GROUP BY m.mentor_id, m.name
            ORDER BY session_count DESC
        """)
        mentor_session_count = cursor.fetchall()

        cursor.execute("""
            SELECT t.topic_name AS topic_name, COUNT(s.session_id) AS session_count
            FROM topics t
            LEFT JOIN sessions s ON t.topic_id = s.topic_id
            GROUP BY t.topic_id, t.topic_name
            ORDER BY session_count DESC
        """)
        popular_topics = cursor.fetchall()

        return jsonify({
            "total_users": total_users,
            "total_mentors": total_mentors,
            "total_schools": total_schools,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "pending_bookings": pending_bookings,
            "bookings_by_school": bookings_by_school,
            "mentor_session_count": mentor_session_count,
            "popular_topics": popular_topics
        }), 200

    finally:
        cursor.close()
        conn.close()
