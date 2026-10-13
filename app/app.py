import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="healthy"), 200

@app.get("/config")
def config():
    return jsonify({
        "app_env": os.getenv("APP_ENV", "not-set"),
        "app_port": os.getenv("APP_PORT", "not-set"),
        "app_color": os.getenv("APP_COLOR", "not-set"),
        "db_username_configured": bool(os.getenv("DB_USERNAME")),
        "db_password_configured": bool(os.getenv("DB_PASSWORD"))
    }), 200

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
