import sqlite3
import os
import hashlib
import click
from flask import Flask, request, g
from dotenv import load_dotenv
import jsonlines
from datetime import datetime
import json
from urllib.parse import urlparse

load_dotenv()
DATABASE = os.getenv('DATABASE')
# TODO: current implementation is closer to a pepper
SALT = os.getenv('SALT')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def client_ip(request):
    return request.remote_addr


"""adapted from https://github.com/HermanMartinus/bearblog/blob/master/blogs/helpers.py#L121"""
def salt_and_hash(request, duration='day'):
    ip = client_ip(request)
    if duration == 'year':
        ip_date_salt_string = f"{ip}-{datetime.now().year}-{SALT}"
    else:
        ip_date_salt_string = f"{ip}-{datetime.now().date()}-{SALT}"

    hash_id = hashlib.sha256(
        ip_date_salt_string.encode('utf-8')
    ).digest()
    return hash_id

def query_db(query, args=(), one=False):
    print(args)
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_feed(domain):
    return query_db("SELECT id FROM feeds WHERE domain = ?", args=[domain], one=True)

def insert_feed(domain, feed_url):
    con = get_db()
    con.execute("INSERT INTO feeds (domain, feed_url) VALUES (?, ?)", [domain, feed_url])
    con.commit()

def get_report(feed_id, hash_id):
    return query_db("SELECT hash_id FROM reports WHERE feed_id = ? AND hash_id = ?", args=[feed_id, hash_id], one=True)

def insert_report(feed_id, hash_id):
    con = get_db()
    con.execute("INSERT INTO reports (feed_id, hash_id) VALUES (?, ?)", [feed_id, hash_id])
    con.commit()

app = Flask(__name__)

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
    feed = get_feed(domain)
    if feed is None:
        return {"message": "Unknown domain"}, 400

    hash_id = salt_and_hash(request, 'year')

    print(feed['id'], hash_id.hex())
    report = get_report(feed['id'], hash_id)
    if report is not None:
        return {"message": "Report already computed"}

    insert_report(feed['id'], hash_id)

    return {"message": "Report registered"}, 201


@app.cli.command("import-feeds")
@click.argument("file_path")
def import_feeds(file_path):
    """Import feeds from a .jsonl file. `domain` and `rss_url` are required."""
    errors = []
    with jsonlines.open(file_path) as reader:
        for obj in reader:
            domain = obj.get("domain")
            rss_url = obj.get("rss_url")
            if rss_url is None:
                errors.append({
                    "domain": domain,
                    "rss_url": rss_url,
                    "error": "missing rss_url"
                })
                continue
            if domain is None:
                domain = urlparse(rss_url).netloc
            try:
                insert_feed(domain, rss_url)
            except sqlite3.IntegrityError:
                # duplicated feed_url, ignore silently
                continue
    if len(errors) > 0:
        print(json.dumps(errors, indent=2))
