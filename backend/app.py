import os
from flask import Flask, request, g
from flask_cors import CORS
from dotenv import load_dotenv
from functions import salt_and_hash
from cli import register_cli
from db import get_feed_by_domain, get_report, delete_report, insert_report


load_dotenv()

CORS_ORIGIN = os.environ['CORS_ORIGIN']

app = Flask(__name__)
register_cli(app)
CORS(app, origins=[CORS_ORIGIN])

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/report", methods=['POST'])
def report():
    payload = request.get_json()
    domain = payload.get("domain")
    if not domain:
        return {"message": "Missing domain"}, 400
    feed = get_feed_by_domain(domain)
    if feed is None:
        return {"message": "Unknown domain"}, 400

    hash_id = salt_and_hash(request, 'year')

    report = get_report(feed['id'], hash_id)

    if report is not None:
        delete_report(feed['id'], hash_id)
        return {"message": "Report deleted"}, 200

    insert_report(feed['id'], hash_id)
    return {"message": "Report registered"}, 201


