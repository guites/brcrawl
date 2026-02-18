-- feed_status table
CREATE TABLE IF NOT EXISTS feed_status (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
);

-- default statuses
INSERT INTO feed_status (name) VALUES ('verified'), ('crawled'), ('suggested'), ('blocked');

-- feeds table
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    feed_url TEXT NOT NULL,
    status_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (status_id) REFERENCES feed_status(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_feed_url
    ON feeds(feed_url);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_domain
    ON feeds(domain);

-- feed status history
CREATE TABLE IF NOT EXISTS feed_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    descr TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (status_id) REFERENCES feed_status(id)
    FOREIGN KEY (feed_id) REFERENCES feeds(id)
);

-- reports table
CREATE TABLE IF NOT EXISTS reports (
    feed_id INTEGER NOT NULL,
    hash_id BLOB NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (feed_id, hash_id),
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE

    CHECK (length(hash_id) = 32)
);

-- crawls table; each feed can have multiple crawls
CREATE TABLE IF NOT EXISTS feed_crawls (
    feed_id INTEGER NOT NULL,
    crawled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE
);

-- domain blocklist; urls that have no valid rss feed
CREATE TABLE IF NOT EXISTS blocklist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_blocklist_domain
    ON blocklist(domain);