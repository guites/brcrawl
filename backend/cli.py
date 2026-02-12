import jsonlines
import click
from urllib.parse import urlparse
import json
import sqlite3
from db import insert_feed
import enum

# TODO: feeds table should have current_status
# but we could also keep a feed_status_history table
# to track when we first discovered something, when it was
# blocked, when it was suggested, etc

class FeedStatus(enum.Enum):
    VERIFIED = 1
    CRAWLED = 2
    SUGGESTED = 3
    BLOCKED = 4

def register_cli(app):
    @app.cli.command("import-feeds")
    @click.argument("file_path")
    @click.option("--feed-status", required=True, type=click.Choice(FeedStatus, case_sensitive=False))
    def import_feeds(file_path, feed_status: FeedStatus):
        """Import feeds from a .jsonl file.
        
        {"domain":"example.com", "rss_url":"https://example.com/feed"}
        
        feed_status is used to track whether the list of feeds has been verified
        by a human (`verified`), crawled by the bot (`crawled`),
        suggested by a third party (`suggested`) or should be removed
        from the system (`blocked`)"""
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

                if domain == '':
                    errors.append({
                        "domain": domain,
                        "rss_url": rss_url,
                        "error": "improper rss_url (probably missing scheme)"
                    })
                    continue

                # deduplicate the feed url by removing trailing slashes
                rss_url = rss_url.rstrip('/')
                try:
                    insert_feed(domain, rss_url, feed_status.value)
                except sqlite3.IntegrityError:
                    # duplicated feed_url, ignore silently
                    continue
        if len(errors) > 0:
            print(json.dumps(errors, indent=2))