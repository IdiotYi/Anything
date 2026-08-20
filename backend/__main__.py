"""Run the local Anything API with python -m backend."""

from .app import app


if __name__ == "__main__":
    print("Anything API: http://127.0.0.1:5000")
    print("Frontend: http://127.0.0.1:8000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
