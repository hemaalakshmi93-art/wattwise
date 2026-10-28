"""WattWise backend: Flask + SQLite REST API for the Mission LiFE prototype."""
import os
from pathlib import Path

from flask import Flask, jsonify

from . import db as database
from .validators import ApiError

BASE_DIR = Path(__file__).resolve().parent.parent


def _float_env(name, default):
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


def create_app(test_config=None):
    try:
        from dotenv import load_dotenv

        load_dotenv(BASE_DIR / ".env")
    except ImportError:  # python-dotenv is optional
        pass

    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("WATTWISE_DB", str(BASE_DIR / "instance" / "wattwise.db")),
        # kg CO2e per kWh of grid electricity. Configurable; verify the latest
        # published CEA (Central Electricity Authority) value before final use.
        EMISSION_FACTOR=_float_env("WATTWISE_EMISSION_FACTOR", 0.82),
        # kg CO2e per km for an assumed average petrol car (optional transport input).
        TRANSPORT_FACTOR=_float_env("WATTWISE_TRANSPORT_FACTOR", 0.17),
        # Rule-of-thumb threshold used by the recommendation engine (kWh per person per month).
        PER_PERSON_THRESHOLD=_float_env("WATTWISE_PER_PERSON_THRESHOLD", 100),
        CORS_ORIGIN=os.environ.get("WATTWISE_CORS_ORIGIN", "http://localhost:5173"),
        ADAPTION_API_URL=os.environ.get("ADAPTION_API_URL", ""),
        ADAPTION_API_KEY=os.environ.get("ADAPTION_API_KEY", ""),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    database.init_app(app)
    with app.app_context():
        database.init_db()

    from .routes import bp

    app.register_blueprint(bp)

    if os.environ.get("WATTWISE_SEED_DEMO") == "1":
        from .demo import seed_demo

        with app.app_context():
            seed_demo(database.get_db())

    # Serve the built React app (frontend/dist) from the same server when it exists.
    dist = Path(os.environ.get("WATTWISE_FRONTEND_DIST", BASE_DIR.parent / "frontend" / "dist"))
    if dist.is_dir():
        from flask import send_from_directory

        @app.get("/", defaults={"path": ""})
        @app.get("/<path:path>")
        def frontend(path):
            if path.startswith("api/"):
                return jsonify({"error": {"message": "Resource not found."}}), 404
            if path and (dist / path).is_file():
                return send_from_directory(dist, path)
            return send_from_directory(dist, "index.html")

    @app.after_request
    def add_cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = app.config["CORS_ORIGIN"]
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
        return resp

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        body = {"error": {"message": err.message}}
        if err.fields:
            body["error"]["fields"] = err.fields
        return jsonify(body), err.status

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": {"message": "Resource not found."}}), 404

    @app.errorhandler(405)
    def not_allowed(_):
        return jsonify({"error": {"message": "Method not allowed."}}), 405

    @app.errorhandler(Exception)
    def unexpected(err):
        app.logger.exception("Unhandled error: %s", err)
        return jsonify({"error": {"message": "Unexpected server error."}}), 500

    return app
