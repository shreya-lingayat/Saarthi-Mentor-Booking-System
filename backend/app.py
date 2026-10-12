from flask import Flask, jsonify
from flask_cors import CORS

from db import get_db_connection
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.school_routes import school_bp
from routes.mentor_routes import mentor_bp
from routes.topic_routes import topic_bp
from routes.session_routes import session_bp
from routes.booking_routes import booking_bp
from routes.feedback_routes import feedback_bp
from routes.analytics_routes import analytics_bp

app = Flask(__name__)

# Allow frontend cross-origin requests
CORS(app)

# Register route blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(school_bp, url_prefix="/api/school")
app.register_blueprint(mentor_bp, url_prefix="/api/mentor")
app.register_blueprint(topic_bp, url_prefix="/api/topics")
app.register_blueprint(session_bp, url_prefix="/api/sessions")
app.register_blueprint(booking_bp, url_prefix="/api/bookings")
app.register_blueprint(feedback_bp, url_prefix="/api/feedback")
app.register_blueprint(analytics_bp, url_prefix="/api/analytics")


@app.route("/")
def home():
    return jsonify({
        "message": "Mentor Session Booking System API is running"
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Database connection test endpoint.
    Tests live MySQL connection without exposing credentials.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "ok",
            "database": "connected"
        }), 200
    except Exception:
        return jsonify({
            "status": "error",
            "database": "disconnected"
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )