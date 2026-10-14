import os
from flask import Flask, jsonify

app = Flask(__name__)


def get_app_port():
    """Read and validate the application port."""
    raw_port = os.getenv("APP_PORT", "8080")

    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError(
            f"APP_PORT must be an integer; received {raw_port!r}"
        ) from exc

    if not 1 <= port <= 65535:
        raise ValueError("APP_PORT must be between 1 and 65535")

    return port


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


@app.get("/config")
def config():
    return jsonify({
        "app_env": os.getenv("APP_ENV", "not-set"),
        "app_port": os.getenv("APP_PORT", "8080"),
        "app_color": os.getenv("APP_COLOR", "not-set"),
        "db_username_configured": bool(os.getenv("DB_USERNAME")),
        "db_password_configured": bool(os.getenv("DB_PASSWORD"))
    }), 200


if __name__ == "__main__":
    port = get_app_port()
    app.run(host="0.0.0.0", port=port)
