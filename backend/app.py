import os
import math
import secrets
from datetime import datetime, timezone
from flask import Flask, render_template, request, g
from flask_cors import CORS
from dotenv import load_dotenv
from functions import salt_and_hash
from cli import register_cli
from db import (
    get_feed_by_domain,
    get_report,
    delete_report,
    insert_report,
    get_latest_feed_items,
    get_latest_feed_items_count,
)


load_dotenv()

CORS_ORIGIN = os.environ["CORS_ORIGIN"]

app = Flask(__name__)
register_cli(app)
CORS(app, origins=[CORS_ORIGIN])


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/report", methods=["POST"])
def report():
    payload = request.get_json()
    domain = payload.get("domain")
    if not domain:
        return {"message": "Missing domain"}, 400
    feed = get_feed_by_domain(domain)
    if feed is None:
        return {"message": "Unknown domain"}, 400

    hash_id = salt_and_hash(request, "year")

    report = get_report(feed["id"], hash_id)

    if report is not None:
        delete_report(feed["id"], hash_id)
        return {"message": "Report deleted"}, 200

    insert_report(feed["id"], hash_id)
    return {"message": "Report registered"}, 201


@app.route("/", methods=["GET"])
def index():
    per_page = 50
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    feed_items = get_latest_feed_items(per_page=per_page, page=page)
    total_items = get_latest_feed_items_count()
    total_pages = max(1, math.ceil(total_items / per_page))
    start_index = (page - 1) * per_page + 1

    # Generate last updated timestamp
    now = datetime.now(timezone.utc)
    last_updated = now.isoformat()
    last_updated_formatted = now.strftime("%d/%m/%Y %H:%M:%S")

    # Generate nonce for CSP
    nonce = secrets.token_hex(16)

    # Get backend URL for CSP
    backend_url = os.environ.get("BACKEND_URL", request.host_url)

    return render_template(
        "views/index.html",
        feed_items=feed_items,
        current_page=page,
        total_pages=total_pages,
        start_index=start_index,
        last_updated=last_updated,
        last_updated_formatted=last_updated_formatted,
        nonce=nonce,
        backend_url=backend_url,
    )


@app.route("/about", methods=["GET"])
def about():
    # Generate last updated timestamp
    now = datetime.now(timezone.utc)
    last_updated = now.isoformat()
    last_updated_formatted = now.strftime("%d/%m/%Y %H:%M:%S")

    # Generate nonce for CSP
    nonce = secrets.token_hex(16)

    # Get backend URL for CSP
    backend_url = os.environ.get("BACKEND_URL", request.host_url)

    return render_template(
        "views/about.html",
        last_updated=last_updated,
        last_updated_formatted=last_updated_formatted,
        nonce=nonce,
        backend_url=backend_url,
    )
