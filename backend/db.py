from flask import g
import sqlite3
import os
DATABASE = os.environ['DATABASE']


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_feed_by_domain(domain):
    return query_db("SELECT f.id as id, domain, feed_url, status_id, fs.name as feed_status, created_at FROM feeds f INNER JOIN feed_status fs ON f.status_id = fs.id WHERE domain = ?", args=[domain], one=True)

def get_feed_by_url(feed_url):
    return query_db("SELECT f.id as id, domain, feed_url, fs.name as feed_status, created_at FROM feeds f INNER JOIN feed_status fs ON f.status_id = fs.id WHERE f.feed_url = ?", [feed_url], one=True)

def get_feed_by_id(feed_id):
    return query_db("SELECT f.id as id, domain, feed_url, fs.name as feed_status, created_at FROM feeds f INNER JOIN feed_status fs ON f.status_id = fs.id WHERE f.id = ?", [feed_id], one=True)

def get_oldest_crawled_feed():
    return query_db("SELECT f.id as id, domain, feed_url, fs.name as feed_status, created_at FROM feeds f INNER JOIN feed_status fs ON f.status_id = fs.id WHERE f.status_id = 2 ORDER BY created_at ASC", one=True)

def get_stalest_feeds(limit):
    query = "SELECT f.*, MAX(fc.crawled_at) AS last_crawled_at FROM feeds f LEFT JOIN feed_crawls fc ON f.id = fc.feed_id WHERE f.status_id = 1 GROUP BY f.id ORDER BY last_crawled_at ASC"
    if limit:
        query += " LIMIT ?"
        return query_db(query, [limit])
    return query_db(query)

def get_blocked_feeds_description():
    return query_db("SELECT f.domain, fs.name, fsh1.descr FROM feeds f INNER JOIN feed_status fs ON f.status_id = fs.id LEFT JOIN feed_status_history fsh1 ON (f.id = fsh1.feed_id ) LEFT OUTER JOIN feed_status_history fsh2 ON (f.id = fsh2.feed_id AND fsh1.created_at < fsh2.created_at) WHERE f.status_id = 4 ORDER BY fsh1.created_at DESC")

def get_feeds():
    return query_db("SELECT domain FROM feeds")

def update_feed_status(feed_id, new_status):
    con = get_db()
    con.execute("UPDATE feeds SET status_id = ? WHERE id = ?", [new_status, feed_id])
    con.commit()

def insert_feed(domain, feed_url, status_id):
    con = get_db()
    con.execute("INSERT INTO feeds (domain, feed_url, status_id) VALUES (?, ?, ?)", [domain, feed_url, status_id])
    con.commit()

def batch_update_crawled_at(feed_ids):
    con = get_db()
    con.executemany("INSERT INTO feed_crawls (feed_id) VALUES (?)", feed_ids)
    con.commit()

def get_report(feed_id, hash_id):
    return query_db("SELECT hash_id FROM reports WHERE feed_id = ? AND hash_id = ?", args=[feed_id, hash_id], one=True)

def insert_report(feed_id, hash_id):
    con = get_db()
    con.execute("INSERT INTO reports (feed_id, hash_id) VALUES (?, ?)", [feed_id, hash_id])
    con.commit()

def delete_report(feed_id, hash_id):
    con = get_db()
    con.execute("DELETE FROM reports WHERE feed_id = ? AND hash_id = ?", [feed_id, hash_id])
    con.commit()

def insert_feed_history(feed_id, status_id, desc):
    con = get_db()
    con.execute("INSERT INTO feed_status_history (feed_id, status_id, descr) VALUES (?, ?, ?)", [feed_id, status_id, desc])
    con.commit()

def get_blocklist():
    return query_db("SELECT domain FROM blocklist")

def add_to_blocklist(domain):
    con = get_db()
    con.execute("INSERT INTO blocklist (domain) VALUES (?)", [domain])
    con.commit()