from db import (
    get_feeds_for_processing,
    insert_feed_item,
    mark_feed_checked,
    get_id_from_guid,
    update_feed_latest,
    pause_feed_processing,
)
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup


def status_nok(feed):
    """feedparser uses requests lib under the hood, so we can
    mimic its behaviour. see requests/src/requests/models.py:Requests::ok"""
    return feed.status >= 400


def get_feed_title(feed):
    return feed.title if "title" in feed else "untitled"


def get_entry_title(entry):
    return entry.title if "title" in entry else "untitled"


def get_entry_url(entry):
    return entry.link if "link" in entry else None


def get_entry_guid(entry):
    return entry.id if "id" in entry else entry.link


def get_entry_date(entry):
    if "published_parsed" not in entry:
        return None
    return datetime(*entry.published_parsed[:6]).isoformat()


def get_entry_author(entry):
    return entry.author if "author" in entry else ""


def get_entry_content(entry):
    if "content" not in entry:
        return ""
    if len(entry.content) <= 0:
        return ""
    if "value" not in entry.content[0]:
        return ""
    return entry.content[0].value.strip()


def clean_content(html_content):
    """
    From https://www.alexmolas.com/2024/02/05/a-search-engine-in-80-lines.html
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = " ".join(chunk for chunk in chunks if chunk)
    return cleaned_text


def log(msg, level):
    dt = datetime.now().isoformat()[:-7]
    print(f"[{level}] [{dt}] {msg}")


class FeedProcessor:
    """Adapted from github.com/manualdousuario/lerama and git.sr.ht/~lown/openorb"""

    def __init__(self):
        self.num_feeds = 25
        self.min_process_interval = 120

    def run(self):
        feeds = get_feeds_for_processing(self.num_feeds, self.min_process_interval)

        total_feeds = len(feeds)
        if total_feeds == 0:
            log("No feeds for processing", "INFO")
            return
        log(f"Found {total_feeds} feeds for processing", "INFO")

        # TODO: this could be done in parallel
        for feed in feeds:
            self.process(feed)

    def process(self, feed):
        log(
            f"Processing {feed['feed_url']}, last checked: {feed['last_checked_at']}",
            "INFO",
        )
        mark_feed_checked(feed["id"])
        try:
            parsed = feedparser.parse(feed["feed_url"])
        except Exception as e:
            log(f"Unhandled feedparser exception: {e}", "ERROR")
            return

        # Check for bozo first as requests that are unable to complete
        # have no status information. see feedparser/http.py::get
        if parsed.bozo == 1:
            log(
                f"Malformed feed or incomplete request: {parsed.bozo_exception}",
                "ERROR",
            )
            pause_feed_processing(feed["id"])
            return

        if status_nok(parsed):
            log(f"Couldn't download feed: {parsed.status}", "ERROR")
            pause_feed_processing(feed["id"])
            return

        feed_title = get_feed_title(parsed.feed)
        log(f"Feed title: {feed_title}", "INFO")
        log(f"Feed items: {len(parsed.entries)}", "INFO")
        latest_guid = None

        if len(parsed.entries) <= 0:
            log("    Skipping feed. No feed items found.", "ERROR")
            return

        for entry in parsed.entries:
            entry_title = get_entry_title(entry)
            entry_url = get_entry_url(entry)
            entry_guid = get_entry_guid(entry)
            entry_date = get_entry_date(entry)

            entry_author = get_entry_author(entry)
            entry_content = get_entry_content(entry)

            if len(entry_content) != 0:
                entry_content = clean_content(entry_content)
            # TODO: if the entry content lenght is zero we could try
            # TODO: to download it from the entry_url

            if not entry_date or not entry_url:
                log(
                    f"    Skipping {entry_url} ({entry_date}). Invalid link or publication date.",
                    "ERROR",
                )
                continue

            # if we find the latest registered guid, it means
            # from here on entries were already processed
            if feed["last_post_guid"] == entry_guid:
                break

            if latest_guid is None:
                latest_guid = entry_guid

            log(f"    {entry_url} ({entry_date})", "INFO")
            insert_feed_item(
                feed["id"],
                entry_title,
                entry_url,
                entry_guid,
                entry_date,
                entry_author,
                entry_content,
            )

        if latest_guid is None:
            log("    latest_guid wasn't set.", "ERROR")
            return

        latest_feed_item_id = get_id_from_guid(feed["id"], latest_guid)
        update_feed_latest(feed["id"], latest_guid, latest_feed_item_id)
