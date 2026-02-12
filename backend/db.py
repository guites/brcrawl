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

def get_feed(domain):
    return query_db("SELECT id FROM feeds WHERE domain = ?", args=[domain], one=True)

def insert_feed(domain, feed_url, status_id):
    con = get_db()
    con.execute("INSERT INTO feeds (domain, feed_url, status_id) VALUES (?, ?, ?)", [domain, feed_url, status_id])
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
