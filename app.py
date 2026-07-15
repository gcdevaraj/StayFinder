"""
StayFinder – app.py
Main Flask application entry point
"""

import os
from flask import Flask, jsonify, send_file
from flask_cors import CORS

from database import init_db
from routes.auth import auth_bp
from routes.properties import props_bp
from routes.other import (
    reviews_bp, enquiries_bp, govt_bp,
    areas_bp, amenities_bp, admin_bp,
)

def create_app():
    app = Flask(__name__)

    # ── CORS ───────────────────────────────────────────────────────
    CORS(app, resources={
        r"/api/*": {
            "origins": os.getenv("FRONTEND_URL", "*"),
            "methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
        }
    })

    # ── Blueprints ─────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(props_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(enquiries_bp)
    app.register_blueprint(govt_bp)
    app.register_blueprint(areas_bp)
    app.register_blueprint(amenities_bp)
    app.register_blueprint(admin_bp)

    # ── Frontend Index ─────────────────────────────────────────────
    @app.get("/")
    def index():
        return send_file("stayfinder.html")

    # ── Health check ───────────────────────────────────────────────
    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "StayFinder API",
            "version": "1.0.0",
            "env": os.getenv("FLASK_ENV", "development"),
        })

    # ── API index ──────────────────────────────────────────────────
    @app.get("/api")
    def api_index():
        return jsonify({
            "name": "StayFinder API",
            "version": "1.0.0",
            "endpoints": {
                "auth":        "/api/auth",
                "properties":  "/api/properties",
                "reviews":     "/api/properties/<id>/reviews",
                "enquiries":   "/api/enquiries",
                "govtHostels": "/api/govt-hostels",
                "areas":       "/api/areas",
                "amenities":   "/api/amenities",
                "admin":       "/api/admin",
            },
        })

    # ── Global error handlers ──────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Route not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    init_db()
    app = create_app()
    port = int(os.getenv("PORT", 4000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    print(f"\n[Server] StayFinder API running on http://localhost:{port}")
    print(f"  Health:    http://localhost:{port}/health")
    print(f"  API index: http://localhost:{port}/api\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
