"""Flask application factory and local development entry point."""

from flask import Flask
from flask_cors import CORS

from .config import CORS_ORIGINS
from .routes import api
from .services import MovieService


def create_app(service=None):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})
    app.extensions["movie_service"] = service or MovieService()
    app.register_blueprint(api)
    return app


app = create_app()


if __name__ == "__main__":
    print("Anything API: http://127.0.0.1:5000")
    print("Frontend: http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
