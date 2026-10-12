from functools import wraps
from flask import request, jsonify
import jwt

from auth import decode_token


def role_required(*allowed_roles):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                return jsonify({
                    "error": "Authorization token required"
                }), 401

            try:
                parts = auth_header.split(" ")
                if len(parts) != 2 or parts[0].lower() != "bearer":
                    return jsonify({
                        "error": "Invalid Authorization header format format. Expected Bearer <token>"
                    }), 401

                token = parts[1]
                user = decode_token(token)

                if allowed_roles and user.get("role") not in allowed_roles:
                    return jsonify({
                        "error": "Access denied"
                    }), 403

                request.user = user
                return function(*args, **kwargs)

            except jwt.ExpiredSignatureError:
                return jsonify({
                    "error": "Token has expired"
                }), 401
            except Exception:
                return jsonify({
                    "error": "Invalid or expired token"
                }), 401

        return wrapper
    return decorator