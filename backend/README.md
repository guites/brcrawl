Generate SALT with

```
import secrets
import base64

salt = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
```
