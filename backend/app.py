"""Flask application factory and local development entry point."""

import os
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .config import CORS_ORIGINS
from .routes import api
from .services import MovieService

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(service=None):
    app = Flask(
        __name__,
        static_folder=str(FRONTEND_DIR / "assets"),
        static_url_path="/assets",
    )
    app.config["FRONTEND_DIR"] = str(FRONTEND_DIR)
    if CORS_ORIGINS:
        CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})
    app.extensions["movie_service"] = service or MovieService()
    app.register_blueprint(api)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' https: data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'",
        )
        return response

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"Anything: http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
