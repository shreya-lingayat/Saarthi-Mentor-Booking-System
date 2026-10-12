from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required
from utils.validators import is_valid_time_range, check_mentor_conflict, parse_time

session_bp = Blueprint("sessions", __name__)


def serialize_session(session):
    if not session:
        return session
    for k, v in list(session.items()):
        if hasattr(v, 'isoformat'):
            session[k] = str(v)
        elif hasattr(v, 'total_seconds'):
            session[k] = parse_time(v)
    return session


@session_bp.route("", methods=["GET"])
def get_sessions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT s.*, t.topic_name AS topic_name
            FROM sessions s
            LEFT JOIN topics t ON s.topic_id = t.topic_id
            ORDER BY s.session_date DESC, s.start_time ASC
        """
        cursor.execute(query)
        sessions = cursor.fetchall()
        for s in sessions:
            serialize_session(s)
        return jsonify(sessions), 200
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>", methods=["GET"])
def get_session_by_id(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT s.*, t.topic_name AS topic_name
            FROM sessions s
            LEFT JOIN topics t ON s.topic_id = t.topic_id
            WHERE s.session_id = %s
        """
        cursor.execute(query, (session_id,))
        session = cursor.fetchone()
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        serialize_session(session)

        cursor.execute(
            """
            SELECT m.mentor_id, m.name, m.expertise
            FROM session_mentors sm
            JOIN mentors m ON sm.mentor_id = m.mentor_id
            WHERE sm.session_id = %s
            """,
            (session_id,)
        )
        session["mentors"] = cursor.fetchall()

        return jsonify(session), 200
    finally:
        cursor.close()
        conn.close()


@session_bp.route("", methods=["POST"])
@role_required("admin", "school")
def create_session():
    data = request.get_json() or {}

    topic_id = data.get("topic_id")
    title = data.get("title")
    description = data.get("description", "")
    session_date = data.get("session_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    mode = data.get("mode", "online")
    location = data.get("location", "")
    max_participants = data.get("max_participants", 50)
    status = data.get("status", "open")

    if not title or not session_date or not start_time or not end_time:
        return jsonify({
            "error": "Title, session_date, start_time, and end_time are required"
        }), 400

    if not is_valid_time_range(start_time, end_time):
        return jsonify({
            "error": "Invalid time range: end_time must be strictly after start_time"
        }), 400

    if mode not in ["online", "offline"]:
        return jsonify({"error": "Mode must be 'online' or 'offline'"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        created_by = request.user["user_id"]
        cursor.execute(
            """
            INSERT INTO sessions
            (created_by, topic_id, title, description, session_date, start_time, end_time, mode, location, max_participants, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (created_by, topic_id, title, description, session_date, parse_time(start_time), parse_time(end_time), mode, location, max_participants, status)
        )
        conn.commit()
        session_id = cursor.lastrowid

        return jsonify({
            "message": "Session created successfully",
            "session_id": session_id
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>", methods=["PUT"])
@role_required("admin", "school")
def update_session(session_id):
    data = request.get_json() or {}

    title = data.get("title")
    description = data.get("description")
    session_date = data.get("session_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    mode = data.get("mode")
    location = data.get("location")
    max_participants = data.get("max_participants")
    status = data.get("status")

    if start_time and end_time and not is_valid_time_range(start_time, end_time):
        return jsonify({
            "error": "Invalid time range: end_time must be strictly after start_time"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"error": "Session not found"}), 404

        new_date = session_date or str(existing["session_date"])
        new_st = parse_time(start_time) if start_time else parse_time(existing["start_time"])
        new_et = parse_time(end_time) if end_time else parse_time(existing["end_time"])

        if new_et <= new_st:
            return jsonify({"error": "Invalid time range: end_time must be strictly after start_time"}), 400

        cursor.execute(
            """
            UPDATE sessions
            SET topic_id = COALESCE(%s, topic_id),
                title = COALESCE(%s, title),
                description = COALESCE(%s, description),
                session_date = %s,
                start_time = %s,
                end_time = %s,
                mode = COALESCE(%s, mode),
                location = COALESCE(%s, location),
                max_participants = COALESCE(%s, max_participants),
                status = COALESCE(%s, status)
            WHERE session_id = %s
            """,
            (
                data.get("topic_id"), title, description,
                new_date, new_st, new_et,
                mode, location, max_participants, status,
                session_id
            )
        )
        conn.commit()
        return jsonify({"message": "Session updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>", methods=["DELETE"])
@role_required("admin")
def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM session_mentors WHERE session_id = %s", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
        conn.commit()
        return jsonify({"message": "Session deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>/mentors", methods=["POST"])
@role_required("admin", "mentor")
def assign_mentor(session_id):
    data = request.get_json() or {}
    mentor_id = data.get("mentor_id")

    if not mentor_id:
        return jsonify({"error": "mentor_id is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
        session = cursor.fetchone()
        if not session:
            return jsonify({"error": "Session not found"}), 404

        cursor.execute(
            "SELECT * FROM session_mentors WHERE session_id = %s AND mentor_id = %s",
            (session_id, mentor_id)
        )
        if cursor.fetchone():
            return jsonify({"error": "Mentor is already assigned to this session"}), 409

        has_conflict, message = check_mentor_conflict(
            conn, mentor_id, session["session_date"], session["start_time"], session["end_time"], exclude_session_id=session_id
        )
        if has_conflict:
            return jsonify({"error": message}), 409

        cursor.execute(
            "INSERT INTO session_mentors (session_id, mentor_id) VALUES (%s, %s)",
            (session_id, mentor_id)
        )
        conn.commit()

        return jsonify({"message": "Mentor assigned to session successfully"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>/mentors/<int:mentor_id>", methods=["DELETE"])
@role_required("admin")
def remove_mentor(session_id, mentor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "DELETE FROM session_mentors WHERE session_id = %s AND mentor_id = %s",
            (session_id, mentor_id)
        )
        conn.commit()
        return jsonify({"message": "Mentor unassigned from session"}), 200
    finally:
        cursor.close()
        conn.close()


@session_bp.route("/<int:session_id>/mentors", methods=["GET"])
def get_session_mentors(session_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT m.mentor_id, m.name, m.expertise, m.qualification
            FROM session_mentors sm
            JOIN mentors m ON sm.mentor_id = m.mentor_id
            WHERE sm.session_id = %s
            """,
            (session_id,)
        )
        mentors = cursor.fetchall()
        return jsonify(mentors), 200
    finally:
        cursor.close()
        conn.close()
