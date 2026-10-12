from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT user_id, username, email, role, is_active, created_at, updated_at
            FROM users
            ORDER BY user_id DESC
        """)
        users = cursor.fetchall()
        return jsonify(users), 200
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/users/<int:user_id>/status", methods=["PUT"])
@role_required("admin")
def update_user_status(user_id):
    data = request.get_json() or {}
    is_active = data.get("is_active")

    if is_active is None:
        return jsonify({"error": "is_active boolean field is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE users SET is_active = %s WHERE user_id = %s",
            (1 if is_active else 0, user_id)
        )
        conn.commit()
        return jsonify({"message": f"User status updated to {'active' if is_active else 'inactive'}"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/mentors", methods=["GET"])
@role_required("admin")
def get_mentors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.mentor_id, m.user_id, m.name, m.expertise, m.qualifications, u.username, u.email, u.is_active
            FROM mentors m
            JOIN users u ON m.user_id = u.user_id
        """)
        mentors = cursor.fetchall()
        return jsonify(mentors), 200
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/schools", methods=["GET"])
@role_required("admin")
def get_schools():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT s.school_id, s.user_id, s.organization_name, u.username, u.email, u.is_active
            FROM schools s
            JOIN users u ON s.user_id = u.user_id
        """)
        schools = cursor.fetchall()
        return jsonify(schools), 200
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/bookings", methods=["GET"])
@role_required("admin")
def get_bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.booking_id, b.status, b.created_at,
                   s.organization_name AS school_name,
                   sess.title AS session_title, sess.session_date, sess.start_time, sess.end_time
            FROM bookings b
            LEFT JOIN schools s ON b.school_id = s.school_id
            LEFT JOIN sessions sess ON b.session_id = sess.session_id
            ORDER BY b.booking_id DESC
        """)
        bookings = cursor.fetchall()
        
        # Serialize datetime objects to string
        for b in bookings:
            for k, v in list(b.items()):
                if hasattr(v, 'isoformat'):
                    b[k] = str(v)
        return jsonify(bookings), 200
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/feedback", methods=["GET"])
@role_required("admin")
def get_feedback():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT f.feedback_id, f.booking_id, f.rating, f.comments, f.created_at,
                   s.organization_name AS school_name,
                   sess.title AS session_title
            FROM feedback f
            LEFT JOIN bookings b ON f.booking_id = b.booking_id
            LEFT JOIN schools s ON b.school_id = s.school_id
            LEFT JOIN sessions sess ON b.session_id = sess.session_id
            ORDER BY f.feedback_id DESC
        """)
        feedbacks = cursor.fetchall()
        for f in feedbacks:
            for k, v in list(f.items()):
                if hasattr(v, 'isoformat'):
                    f[k] = str(v)
        return jsonify(feedbacks), 200
    finally:
        cursor.close()
        conn.close()