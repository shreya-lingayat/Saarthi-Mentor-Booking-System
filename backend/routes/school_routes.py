from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required
from utils.validators import parse_time

school_bp = Blueprint("school", __name__)


def serialize_time(record):
    if not record:
        return record
    for k, v in list(record.items()):
        if hasattr(v, 'isoformat'):
            record[k] = str(v)
        elif hasattr(v, 'total_seconds'):
            record[k] = parse_time(v)
    return record


@school_bp.route("/profile", methods=["GET"])
@role_required("school")
def get_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.*, u.username, u.email
            FROM schools s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.user_id = %s
            """,
            (request.user["user_id"],)
        )
        profile = cursor.fetchone()
        if not profile:
            return jsonify({"error": "School profile not found"}), 404
        return jsonify(profile), 200
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/profile", methods=["PUT"])
@role_required("school")
def update_profile():
    data = request.get_json() or {}
    organization_name = data.get("organization_name") or data.get("name")

    if not organization_name:
        return jsonify({"error": "organization_name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE schools SET organization_name = %s WHERE user_id = %s",
            (organization_name, request.user["user_id"])
        )
        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/sessions", methods=["GET"])
@role_required("school")
def get_sessions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.*, t.topic_name AS topic_name
            FROM sessions s
            LEFT JOIN topics t ON s.topic_id = t.topic_id
            WHERE s.status != 'cancelled'
            ORDER BY s.session_date DESC, s.start_time ASC
            """
        )
        sessions = cursor.fetchall()
        for sess in sessions:
            serialize_time(sess)
        return jsonify(sessions), 200
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/bookings", methods=["POST"])
@role_required("school")
def request_booking():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    notes = data.get("notes", "")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT school_id FROM schools WHERE user_id = %s", (request.user["user_id"],))
        school = cursor.fetchone()
        if not school:
            return jsonify({"error": "School profile not found"}), 404
        school_id = school["school_id"]

        cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
        session_rec = cursor.fetchone()
        if not session_rec:
            return jsonify({"error": "Session not found"}), 404

        cursor.execute(
            "SELECT * FROM bookings WHERE school_id = %s AND session_id = %s AND status NOT IN ('cancelled', 'rejected')",
            (school_id, session_id)
        )
        if cursor.fetchone():
            return jsonify({"error": "A booking request for this session already exists"}), 409

        cursor.execute(
            """
            INSERT INTO bookings (school_id, session_id, status, notes)
            VALUES (%s, %s, 'pending', %s)
            """,
            (school_id, session_id, notes)
        )
        conn.commit()

        return jsonify({
            "message": "Booking request submitted successfully",
            "booking_id": cursor.lastrowid
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/bookings", methods=["GET"])
@role_required("school")
def get_my_bookings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT school_id FROM schools WHERE user_id = %s", (request.user["user_id"],))
        school = cursor.fetchone()
        if not school:
            return jsonify({"error": "School profile not found"}), 404

        cursor.execute(
            """
            SELECT b.booking_id, b.status, b.requested_at AS created_at,
                   sess.session_id, sess.title AS session_title, sess.session_date, sess.start_time, sess.end_time, sess.mode, sess.location,
                   t.topic_name AS topic_name,
                   f.feedback_id, f.rating, f.comments AS feedback_comments
            FROM bookings b
            JOIN sessions sess ON b.session_id = sess.session_id
            LEFT JOIN topics t ON sess.topic_id = t.topic_id
            LEFT JOIN feedback f ON b.booking_id = f.booking_id
            WHERE b.school_id = %s
            ORDER BY b.booking_id DESC
            """,
            (school["school_id"],)
        )
        bookings = cursor.fetchall()
        for b in bookings:
            serialize_time(b)
        return jsonify(bookings), 200
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
@role_required("school")
def cancel_booking(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT school_id FROM schools WHERE user_id = %s", (request.user["user_id"],))
        school = cursor.fetchone()
        if not school:
            return jsonify({"error": "School profile not found"}), 404

        cursor.execute(
            "SELECT * FROM bookings WHERE booking_id = %s AND school_id = %s",
            (booking_id, school["school_id"])
        )
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found or not owned by school"}), 404

        if booking["status"] in ["completed", "cancelled"]:
            return jsonify({"error": f"Cannot cancel booking with status '{booking['status']}'"}), 400

        cursor.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
            (booking_id,)
        )
        conn.commit()
        return jsonify({"message": "Booking cancelled successfully"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@school_bp.route("/feedback", methods=["POST"])
@role_required("school")
def submit_feedback():
    data = request.get_json() or {}
    booking_id = data.get("booking_id")
    rating = data.get("rating")
    comments = data.get("comments") or data.get("feedback_text", "")

    if not booking_id or rating is None:
        return jsonify({"error": "booking_id and rating are required"}), 400

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400
    except ValueError:
        return jsonify({"error": "Rating must be a number between 1 and 5"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT school_id FROM schools WHERE user_id = %s", (request.user["user_id"],))
        school = cursor.fetchone()
        if not school:
            return jsonify({"error": "School profile not found"}), 404

        school_id = school["school_id"]

        cursor.execute(
            "SELECT * FROM bookings WHERE booking_id = %s AND school_id = %s",
            (booking_id, school_id)
        )
        booking = cursor.fetchone()
        if not booking:
            return jsonify({"error": "Booking not found or does not belong to your school"}), 404

        if booking["status"] != "completed":
            return jsonify({"error": "Feedback can only be submitted for completed sessions"}), 400

        cursor.execute("SELECT feedback_id FROM feedback WHERE booking_id = %s", (booking_id,))
        if cursor.fetchone():
            return jsonify({"error": "Feedback has already been submitted for this booking"}), 409

        cursor.execute(
            "INSERT INTO feedback (booking_id, school_id, rating, comments) VALUES (%s, %s, %s, %s)",
            (booking_id, school_id, rating, comments)
        )
        conn.commit()

        return jsonify({
            "message": "Feedback submitted successfully",
            "feedback_id": cursor.lastrowid
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()