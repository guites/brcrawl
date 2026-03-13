from db import get_feeds_for_processing, insert_feed_item, mark_feed_checked, get_id_from_guid, update_feed_latest
import feedparser

class FeedProcessor:
    """Adapted from github.com/manualdousuario/lerama and git.sr.ht/~lown/openorb"""
    def __init__(self):
        self.num_feeds = 25
        self.min_process_interval = 120

    def run(self):
        feeds = get_feeds_for_processing(self.num_feeds, self.min_process_interval)

        total_feeds = len(feeds)
        if total_feeds == 0:
            print("[INFO] No feeds for processing")
            return
        print(f"[INFO] Found {total_feeds} feeds for processing")

        # TODO: this could be done in parallel
        for feed in feeds:
            print(f"[INFO] Processing {feed['feed_url']}, last checked: {feed['last_checked_at']}")
            self.process(feed)

    def process(self, feed):
        mark_feed_checked(feed['id'])
        parsed = feedparser.parse(feed['feed_url'])
        if parsed.bozo == 1:
            print(f"[ERROR] Malformed feed. Skipping: <{parsed.bozo_exception}>")
            return
        feed_title = parsed.feed.title if "title" in parsed.feed else "(no title found)"
        print(f"[INFO] Feed title: {feed_title}")
        print(f"[INFO] Feed items: {len(parsed.entries)}")
        latest_guid = None
        if len(parsed.entries) <= 0:
            print("    [ERROR] Skipping feed. No feed items found.")
            return

        for entry in parsed.entries:
            if "published_parsed" not in entry:
                print(f"    [ERROR] Skipping <{entry.link}> - no publication date.")
                continue

            if latest_guid is None:
                latest_guid = entry.id if "id" in entry else entry.link

            print(f"    [INFO] <{entry.link} on {entry.published}")
            insert_feed_item(feed['id'], entry)

        if latest_guid is None:
            print("    [ERROR] latest_guid wasn't set.")
            return

        latest_feed_item_id = get_id_from_guid(feed['id'], latest_guid)
        update_feed_latest(feed['id'], latest_guid, latest_feed_item_id)
