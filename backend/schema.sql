-- feeds table
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    feed_url TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_feed_url
    ON feeds(feed_url);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feeds_domain
    ON feeds(domain);

-- reports table
CREATE TABLE IF NOT EXISTS reports (
    feed_id INTEGER NOT NULL,
    hash_id BLOB NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (feed_id, hash_id),
    FOREIGN KEY (feed_id) REFERENCES feeds(id) ON DELETE CASCADE

    CHECK (length(hash_id) = 32)
);

