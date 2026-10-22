from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Dict, Optional

import requests

API_URL = "https://api.producthunt.com/v2/api/graphql"
TOKEN_URL = "https://api.producthunt.com/v2/oauth/token"
log = logging.getLogger(__name__)


class AuthError(RuntimeError):
    pass


class APIError(RuntimeError):
    pass


class PHClient:
    """Product Hunt GraphQL v2 client with rate-limit-aware throttling.

    Auth: PH_TOKEN (developer token) or PH_CLIENT_ID + PH_CLIENT_SECRET (client credentials).
    Fails loudly on auth errors (no mock fallback).
    """

    def __init__(self, token: Optional[str] = None, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None, session: Optional[requests.Session] = None,
                 sleep: Callable[[float], None] = time.sleep, min_remaining: int = 300,
                 max_retries: int = 5, timeout: float = 30):
        self.session = session or requests.Session()
        self.sleep = sleep
        self.min_remaining = min_remaining
        self.max_retries = max_retries
        self.timeout = timeout
        self.token = (token or os.environ.get("PH_TOKEN") or "").strip().strip("'\"") or None
        self.client_id = client_id or os.environ.get("PH_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PH_CLIENT_SECRET")
        if not self.token and not (self.client_id and self.client_secret):
            raise AuthError("Set PH_TOKEN, or PH_CLIENT_ID and PH_CLIENT_SECRET.")

    def _authenticate(self) -> None:
        r = self.session.post(TOKEN_URL, json={
            "client_id": self.client_id, "client_secret": self.client_secret,
            "grant_type": "client_credentials"}, timeout=self.timeout)
        if r.status_code != 200:
            raise AuthError(f"Token request failed with HTTP {r.status_code}")
        tok = r.json().get("access_token")
        if not tok:
            raise AuthError("Token response had no access_token")
        self.token = tok

    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.token:
            self._authenticate()
        attempt = 0
        while True:
            r = self.session.post(API_URL, json={"query": query, "variables": variables or {}},
                                  headers={"Authorization": f"Bearer {self.token}",
                                           "Accept": "application/json"}, timeout=self.timeout)
            if r.status_code == 429 or r.status_code >= 500:
                attempt += 1
                if attempt > self.max_retries:
                    raise APIError(f"Giving up after {self.max_retries} retries (HTTP {r.status_code})")
                wait = _int(r.headers.get("X-Rate-Limit-Reset")) if r.status_code == 429 else None
                wait = (wait + 2) if wait is not None else min(2 ** attempt, 60)
                log.warning("HTTP %s, waiting %ss (retry %s)", r.status_code, wait, attempt)
                self.sleep(wait)
                continue
            if r.status_code == 401:
                code = ""
                try:
                    code = (r.json().get("errors") or [{}])[0].get("error", "")
                except ValueError:
                    pass
                raise AuthError(f"Unauthorized (HTTP 401{', ' + code if code else ''}). Use the "
                                "'Developer Token' from producthunt.com/v2/oauth/applications, "
                                "not the API key/secret.")
            if r.status_code != 200:
                raise APIError(f"HTTP {r.status_code}: {r.text[:200]}")
            self._throttle(r.headers)
            data = r.json()
            if data.get("errors"):
                raise APIError(f"GraphQL errors: {data['errors']}")
            return data.get("data") or {}

    def _throttle(self, headers) -> None:
        remaining = _int(headers.get("X-Rate-Limit-Remaining"))
        reset = _int(headers.get("X-Rate-Limit-Reset"))
        if remaining is not None and reset is not None and remaining < self.min_remaining:
            log.info("Rate-limit remaining %s < %s; sleeping %ss", remaining, self.min_remaining, reset + 1)
            self.sleep(reset + 1)


def _int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
