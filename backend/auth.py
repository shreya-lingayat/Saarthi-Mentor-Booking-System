import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from config import JWT_SECRET


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


def generate_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm="HS256"
    )


def decode_token(token):
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"]
    )