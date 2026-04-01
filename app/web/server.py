from pathlib import Path
from flask import Flask, jsonify, send_from_directory

from app.web.state import get_state

PROJECT_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_DIR / "static"
ASSETS_DIR = PROJECT_DIR / "assets"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/state")
def api_state():
    return jsonify(get_state())


@app.get("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)


@app.get("/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_DIR, filename)


def run_server(host="127.0.0.1", port=8000):
    app.run(host=host, port=port, debug=False, use_reloader=False)