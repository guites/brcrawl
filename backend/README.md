# BRCrawl backend server

Install dependencies with `uv sync`.

Generate SALT with:

```python
import secrets
import base64

salt = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
```

Create .env file:

```text
SALT=generatedwithcommandabove
DATABASE='brcrawl.sqlite3'
CORS_ORIGIN='https://backend.com
```

Run webserver locally with:

```bash
uv run flask run
```

## Running the project

1. Create the database from the schema.sql file:

    ```bash
    sqlite3 brcrawl.sqlite3 < schema.sql
    ```

1. Import some feeds via the command line:

    Save the block below as initial_feeds.jsonl.

    ```jsonl
    {"domain": "guilhermegarcia.dev","rss_url": "https://guilhermegarcia.dev/index.xml"}
    {"domain": "ararinhaaazul.bearblog.dev","rss_url": "https://ararinhaaazul.bearblog.dev/index.xml"}
    {"domain": "ruadafeira.bearblog.dev","rss_url": "https://ruadafeira.bearblog.dev/index.xml"}
    {"domain": "ththoughtz.bearblog.dev","rss_url": "https://ththoughtz.bearblog.dev/index.xml"}
    {"domain": "nellehblog.bearblog.dev","rss_url": "https://nellehblog.bearblog.dev/index.xml"}
    {"domain": "blogdoth.com.br","rss_url": "https://blogdoth.com.br/index.xml"}
    {"domain": "curadoria.bearblog.dev","rss_url": "https://curadoria.bearblog.dev/index.xml"}
    {"domain": "spirit.bearblog.dev","rss_url": "https://spirit.bearblog.dev/index.xml"}
    {"domain": "leandromaciel.bearblog.dev","rss_url": "https://leandromaciel.bearblog.dev/index.xml"}
    ```

    Import it using the `import-feeds`  command:

    ```bash
    uv run flask import-feeds initial_feeds.jsonl --feed-status verified
    ```

1. Run the processor to access registered feeds and save blog posts locally.

    ```bash
    uv run process-feeds
    ```

Now you'll have plenty of data for initial analysis.
