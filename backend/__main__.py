"""Run Anything locally with ``python -m backend``."""

import os

from .app import app


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"Anything: http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
