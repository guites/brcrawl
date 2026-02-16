import jsonlines
import click
from urllib.parse import urlparse
import json
import sqlite3
from db import insert_feed, batch_update_crawled_at, get_feed_by_domain, get_feed_by_url, get_feeds_most_recent_crawl_date, get_oldest_crawled_feed, update_feed_status, get_feeds
import enum
import pyperclip

# TODO: feeds table should have current_status
# but we could also keep a feed_status_history table
# to track when we first discovered something, when it was
# blocked, when it was suggested, etc

class FeedStatus(enum.Enum):
    VERIFIED = 1
    CRAWLED = 2
    SUGGESTED = 3
    BLOCKED = 4

class ShortFeedStatus(enum.Enum):
    V = 1
    C = 2
    S = 3
    B = 4


def register_cli(app):
    @app.cli.command("import-feeds")
    @click.argument("file_path")
    @click.option("--feed-status", required=True, type=click.Choice(FeedStatus, case_sensitive=False))
    @click.option("--output")
    def import_feeds(file_path, feed_status: FeedStatus, output):
        """Import feeds from a .jsonl file.

        {"domain":"example.com", "rss_url":"https://example.com/feed"}

        feed_status is used to track whether the list of feeds has been verified
        by a human (`verified`), crawled by the bot (`crawled`),
        suggested by a third party (`suggested`) or should be removed
        from the system (`blocked`)"""
        report = { "errors": [], "logs": [] }
        with jsonlines.open(file_path) as reader:
            for obj in reader:
                domain = obj.get("domain")
                rss_url = obj.get("rss_url")
                if rss_url is None:
                    report['errors'].append({
                        "domain": domain,
                        "rss_url": rss_url,
                        "error": "missing rss_url"
                    })
                    continue

                if domain is None:
                    domain = urlparse(rss_url).netloc

                if domain == '':
                    report['errors'].append({
                        "domain": domain,
                        "rss_url": rss_url,
                        "error": "improper rss_url (probably missing scheme)"
                    })
                    continue

                # deduplicate the feed url by removing trailing slashes
                rss_url = rss_url.rstrip('/')
                try:
                    insert_feed(domain, rss_url, feed_status.value)
                    report['logs'].append(
                        {
                            "domain": domain,
                            "rss_url": rss_url,
                            "logs": "Added"
                        }
                    )
                except sqlite3.IntegrityError:
                    report['logs'].append(
                        {
                            "domain": domain,
                            "rss_url": rss_url,
                            "log": "Duplicated"
                        }
                    )
                    continue
        if output:
            with open(output, "w", encoding='utf-8') as w:
                json.dump(report, w, indent=2)
        else:
            print(json.dumps(report, indent=2))

    @app.cli.command("find-feed")
    @click.option("--feed", required=False)
    @click.option("--domain", required=False)
    def find_feed(feed, domain):
        """Finds a feed by either feed_url or domain.

        If neither are provided, returns the oldest registered feed
        with `crawled` status.

        The found domain is automatically copied to the system clipboard."""
        if feed and domain:
            raise click.UsageError("--feed and --domain are mutually exclusive")
        feed_obj = None
        if feed:
            feed_obj = get_feed_by_url(feed)
            if not feed_obj:
                print("Feed not found.")
                return
        if domain:
            feed_obj = get_feed_by_domain(domain)
            if not feed_obj:
                print("Feed not found.")
                return

        # check if no option was selected
        if not feed_obj:
            feed_obj = get_oldest_crawled_feed()
            if not feed_obj:
                print("No 'crawled' feeds left for review.")
                return

        # print feed information
        print(f"id: {feed_obj['id']}")
        print(f"domain: {feed_obj['domain']}")
        print(f"website: https://{feed_obj['domain']}")
        print(f"feed_url: {feed_obj['feed_url']}")
        print(f"feed_status: {feed_obj['feed_status']}")
        print(f"created_at: {feed_obj['created_at']}")
        pyperclip.copy(feed_obj['domain'])

    @app.cli.command("update-feed")
    @click.option("--domain", prompt=True)
    @click.option("--feed-status", prompt=True, type=click.Choice(ShortFeedStatus, case_sensitive=False))
    def update_feed(domain, feed_status):
        """Updates given feed status.

        If either domain or feed_status are not provided,
        user is prompted for the values."""
        feed_obj = get_feed_by_domain(domain)
        old_status = feed_obj['feed_status']
        if not feed_obj:
            print("Feed not found.")
            return
        update_feed_status(feed_obj['id'], feed_status.value)
        feed_obj = get_feed_by_domain(domain)
        new_status = feed_obj['feed_status']
        print(f"Updated {domain} from {old_status} to {new_status}")

    @app.cli.command("crawl-feeds")
    @click.option("--limit")
    @click.option("--output")
    @click.option("--mark-crawled", is_flag=True)
    def crawl_feeds(limit, output, mark_crawled):
        """Lists verified feeds which haven't been crawled for the longest while"""
        feeds = get_feeds_most_recent_crawl_date(limit)
        feeds_obj = [{ "id": feed['id'], "domain": feed['domain'], "feed_url": feed['feed_url'], "crawled_at": feed["crawled_at"]} for feed in feeds]
        if not output:
           for feed in feeds_obj:
               print(json.dumps(feed))
        if output:
            with jsonlines.open(output, "w") as writer:
                writer.write_all(feeds_obj)
        if mark_crawled:
            batch_update_crawled_at([ (feed['id'], ) for feed in feeds ])

    @app.cli.command("known-domains")
    @click.option("--output")
    def known_domains(output):
        """Lists all domains registered on the database"""
        feeds = get_feeds()
        domains_obj = [feed['domain'] for feed in feeds]
        if output:
            with open(output, "w", encoding='utf-8') as w:
                for domain in domains_obj:
                    w.write(f"{domain}\n")
        else:
            for domain in domains_obj:
                print(domain)