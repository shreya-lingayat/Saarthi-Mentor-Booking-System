import hashlib
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from db import get_db_connection
from auth import (
    hash_password,
    verify_password,
    generate_token
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    username = data.get("username")
    email = data.get("email") or f"{username}@example.com"
    password = data.get("password")
    role = data.get("role")

    if not username or not password or not role:
        return jsonify({
            "error": "Username, password and role are required"
        }), 400

    if role not in ["admin", "school", "mentor"]:
        return jsonify({
            "error": "Invalid role. Role must be admin, school, or mentor"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if cursor.fetchone():
            return jsonify({
                "error": "Username or email already exists"
            }), 409

        password_hash = hash_password(password)

        query = """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (%s, %s, %s, %s, 1)
        """
        cursor.execute(query, (username, email, password_hash, role))
        conn.commit()

        user_id = cursor.lastrowid

        if role == "mentor":
            name = data.get("name") or username
            expertise = data.get("expertise") or "General"
            qualification = data.get("qualification") or data.get("qualifications") or "Not specified"
            cursor.execute(
                """
                INSERT INTO mentors (user_id, name, expertise, qualification, email)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, name, expertise, qualification, email)
            )
            conn.commit()

        elif role == "school":
            org_name = data.get("organization_name") or data.get("name") or username
            org_type = data.get("organization_type") or "school"
            if org_type not in ["school", "ngo"]:
                org_type = "school"
            cursor.execute(
                """
                INSERT INTO schools (user_id, organization_name, organization_type, email)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, org_name, org_type, email)
            )
            conn.commit()

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id,
            "role": role
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({
            "error": str(e)
        }), 400

    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    login_id = data.get("username") or data.get("email")
    password = data.get("password")

    if not login_id or not password:
        return jsonify({
            "error": "Username/email and password are required"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT user_id, username, email, password_hash, role, is_active
            FROM users
            WHERE username = %s OR email = %s
            """,
            (login_id, login_id)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "error": "Invalid username or password"
            }), 401

        if user.get("is_active") is not None and user.get("is_active") == 0:
            return jsonify({
                "error": "Account is deactivated. Please contact admin."
            }), 403

        if not verify_password(password, user["password_hash"]):
            return jsonify({
                "error": "Invalid username or password"
            }), 401

        token = generate_token(user["user_id"], user["role"])

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user_id": user["user_id"],
            "role": user["role"]
        }), 200

    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email") or data.get("username")

    if not email:
        return jsonify({"error": "Email or username is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT user_id, email FROM users WHERE email = %s OR username = %s",
            (email, email)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User with specified email/username not found"}), 404

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=1)

        cursor.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, used)
            VALUES (%s, %s, %s, 0)
            """,
            (user["user_id"], token_hash, expires_at)
        )
        conn.commit()

        return jsonify({
            "message": "Password reset token generated",
            "dev_reset_token": raw_token,
            "dev_reset_url": f"reset-password.html?token={raw_token}"
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    raw_token = data.get("token")
    new_password = data.get("new_password") or data.get("password")

    if not raw_token or not new_password:
        return jsonify({"error": "Reset token and new password are required"}), 400

    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, user_id, expires_at, used
            FROM password_reset_tokens
            WHERE token_hash = %s
            """,
            (token_hash,)
        )
        record = cursor.fetchone()

        if not record:
            return jsonify({"error": "Invalid password reset token"}), 400

        if record.get("used") == 1:
            return jsonify({"error": "Token has already been used"}), 400

        if record["expires_at"] < datetime.utcnow():
            return jsonify({"error": "Token has expired"}), 400

        new_hash = hash_password(new_password)

        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (new_hash, record["user_id"])
        )
        cursor.execute(
            "UPDATE password_reset_tokens SET used = 1 WHERE id = %s",
            (record["id"],)
        )
        conn.commit()

        return jsonify({"message": "Password reset successful"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()