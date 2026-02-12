Generate SALT with

```
import secrets
import base64

salt = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
```

Create .env file

```
SALT=generatedwithcommandabove
DATABASE='brcrawl.sqlite3'
CORS_ORIGIN='https://backend.com
```

Run webserver locally with

```
uv run flask run
```
