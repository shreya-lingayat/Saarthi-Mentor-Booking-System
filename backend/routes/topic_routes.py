from flask import Blueprint, jsonify, request

from db import get_db_connection
from utils.decorators import role_required

topic_bp = Blueprint("topics", __name__)


@topic_bp.route("", methods=["GET"])
def get_topics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT topic_id, topic_name AS name, description, is_active, created_at FROM topics ORDER BY topic_id DESC")
        topics = cursor.fetchall()
        for t in topics:
            for k, v in list(t.items()):
                if hasattr(v, 'isoformat'):
                    t[k] = str(v)
        return jsonify(topics), 200
    finally:
        cursor.close()
        conn.close()


@topic_bp.route("", methods=["POST"])
@role_required("admin")
def create_topic():
    data = request.get_json() or {}
    name = data.get("name") or data.get("title") or data.get("topic_name")
    description = data.get("description", "")

    if not name:
        return jsonify({"error": "Topic name/title is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "INSERT INTO topics (topic_name, description, is_active) VALUES (%s, %s, 1)",
            (name, description)
        )
        conn.commit()
        return jsonify({
            "message": "Topic created successfully",
            "topic_id": cursor.lastrowid
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@topic_bp.route("/<int:topic_id>", methods=["PUT"])
@role_required("admin")
def update_topic(topic_id):
    data = request.get_json() or {}
    name = data.get("name") or data.get("title") or data.get("topic_name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Topic name/title is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "UPDATE topics SET topic_name = %s, description = %s WHERE topic_id = %s",
            (name, description, topic_id)
        )
        conn.commit()
        return jsonify({"message": "Topic updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@topic_bp.route("/<int:topic_id>", methods=["DELETE"])
@role_required("admin")
def delete_topic(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM topics WHERE topic_id = %s", (topic_id,))
        conn.commit()
        return jsonify({"message": "Topic deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()
