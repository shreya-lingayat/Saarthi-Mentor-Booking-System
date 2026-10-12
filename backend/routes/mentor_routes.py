from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required
from utils.validators import is_valid_time_range, parse_time

mentor_bp = Blueprint("mentor", __name__)


def serialize_time(record):
    if not record:
        return record
    for k, v in list(record.items()):
        if hasattr(v, 'isoformat'):
            record[k] = str(v)
        elif hasattr(v, 'total_seconds'):
            record[k] = parse_time(v)
    return record


@mentor_bp.route("/profile", methods=["GET"])
@role_required("mentor")
def get_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT m.mentor_id, m.user_id, m.name, m.phone, m.email, m.expertise, m.qualification AS qualifications, m.bio, u.username
            FROM mentors m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.user_id = %s
            """,
            (request.user["user_id"],)
        )
        profile = cursor.fetchone()
        if not profile:
            return jsonify({"error": "Mentor profile not found"}), 404
        return jsonify(profile), 200
    finally:
        cursor.close()
        conn.close()


@mentor_bp.route("/profile", methods=["PUT"])
@role_required("mentor")
def update_profile():
    data = request.get_json() or {}
    name = data.get("name")
    expertise = data.get("expertise")
    qualification = data.get("qualification") or data.get("qualifications")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            UPDATE mentors
            SET name = COALESCE(%s, name),
                expertise = COALESCE(%s, expertise),
                qualification = COALESCE(%s, qualification)
            WHERE user_id = %s
            """,
            (name, expertise, qualification, request.user["user_id"])
        )
        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@mentor_bp.route("/availability", methods=["GET"])
@role_required("mentor")
def get_availability():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ma.*
            FROM mentor_availability ma
            JOIN mentors m ON ma.mentor_id = m.mentor_id
            WHERE m.user_id = %s
            ORDER BY ma.available_date ASC, ma.start_time ASC
            """,
            (request.user["user_id"],)
        )
        slots = cursor.fetchall()
        for s in slots:
            serialize_time(s)
        return jsonify(slots), 200
    finally:
        cursor.close()
        conn.close()


@mentor_bp.route("/availability", methods=["POST"])
@role_required("mentor")
def add_availability():
    data = request.get_json() or {}
    available_date = data.get("available_date") or data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not available_date or not start_time or not end_time:
        return jsonify({"error": "available_date, start_time, and end_time are required"}), 400

    if not is_valid_time_range(start_time, end_time):
        return jsonify({"error": "end_time must be strictly after start_time"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mentor_id FROM mentors WHERE user_id = %s", (request.user["user_id"],))
        mentor = cursor.fetchone()
        if not mentor:
            return jsonify({"error": "Mentor profile not found"}), 404

        mentor_id = mentor["mentor_id"]
        cursor.execute(
            """
            INSERT INTO mentor_availability (mentor_id, available_date, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, 'available')
            """,
            (mentor_id, available_date, parse_time(start_time), parse_time(end_time))
        )
        conn.commit()

        return jsonify({
            "message": "Availability slot added successfully",
            "availability_id": cursor.lastrowid
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@mentor_bp.route("/availability/<int:availability_id>", methods=["PUT"])
@role_required("mentor")
def update_availability(availability_id):
    data = request.get_json() or {}
    available_date = data.get("available_date") or data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if start_time and end_time and not is_valid_time_range(start_time, end_time):
        return jsonify({"error": "end_time must be strictly after start_time"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mentor_id FROM mentors WHERE user_id = %s", (request.user["user_id"],))
        mentor = cursor.fetchone()
        if not mentor:
            return jsonify({"error": "Mentor profile not found"}), 404

        cursor.execute(
            """
            UPDATE mentor_availability
            SET available_date = COALESCE(%s, available_date),
                start_time = COALESCE(%s, start_time),
                end_time = COALESCE(%s, end_time)
            WHERE availability_id = %s AND mentor_id = %s
            """,
            (available_date, parse_time(start_time) if start_time else None, parse_time(end_time) if end_time else None, availability_id, mentor["mentor_id"])
        )
        conn.commit()
        return jsonify({"message": "Availability slot updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@mentor_bp.route("/sessions", methods=["GET"])
@role_required("mentor")
def get_assigned_sessions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT mentor_id FROM mentors WHERE user_id = %s", (request.user["user_id"],))
        mentor = cursor.fetchone()
        if not mentor:
            return jsonify({"error": "Mentor profile not found"}), 404

        cursor.execute(
            """
            SELECT s.session_id, s.title, s.description, s.session_date, s.start_time, s.end_time, s.mode, s.location, s.status,
                   t.topic_name AS topic_name
            FROM sessions s
            JOIN session_mentors sm ON s.session_id = sm.session_id
            LEFT JOIN topics t ON s.topic_id = t.topic_id
            WHERE sm.mentor_id = %s
            ORDER BY s.session_date DESC, s.start_time ASC
            """,
            (mentor["mentor_id"],)
        )
        sessions = cursor.fetchall()
        for s in sessions:
            serialize_time(s)
        return jsonify(sessions), 200
    finally:
        cursor.close()
        conn.close()