import os

from app import create_app
from app.extensions.socketio import socketio

application = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    socketio.run(application, debug=debug, host="0.0.0.0", port=port, use_reloader=debug)
