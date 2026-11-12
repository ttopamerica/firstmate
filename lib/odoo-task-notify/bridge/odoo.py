"""JSON-2 client used by the Odoo task notification commands. Stdlib only.

POST /json/2/<model>/<method>, bearer API key, X-Odoo-Database header.
The key is read from a private file at runtime and is never logged, echoed, or put in an exception message.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

READ_METHODS = frozenset({"search_read", "read", "search_count", "search", "fields_get"})


class OdooError(Exception):
    pass


class Json2:
    def __init__(self, url: str, db: str, api_key: str, timeout: float = 20.0):
        self.url, self.db, self._key, self.timeout = url.rstrip("/"), db, api_key, timeout

    def call(self, model: str, method: str, ids=None, **kwargs):
        body = dict(kwargs)
        if ids is not None:
            body["ids"] = list(ids)
        req = urllib.request.Request(
            f"{self.url}/json/2/{model}/{method}",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self._key}", "X-Odoo-Database": self.db,
                     "Content-Type": "application/json; charset=utf-8"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:  # noqa: S310
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = json.loads(e.read() or b"{}").get("message", "")[:300]
                detail = detail.replace(self._key, "***")
            except Exception:
                pass
            raise OdooError(f"{model}.{method} -> HTTP {e.code} {detail}".strip()) from None
        except urllib.error.URLError as e:
            raise OdooError(f"{model}.{method} -> {type(e.reason).__name__}") from None


class ReadOnly:
    """A transport that refuses every write. Used by the start scan."""

    def __init__(self, inner):
        self.inner = inner

    def call(self, model, method, ids=None, **kw):
        if method not in READ_METHODS:
            raise OdooError(f"read-only transport refused {model}.{method}")
        return self.inner.call(model, method, ids=ids, **kw)
