# SPDX-License-Identifier: MIT
"""An in-memory stand-in for a urllib opener: no sockets are opened."""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

ISSUER = "https://issuer.example"

METADATA: dict[str, Any] = {
    "issuer": ISSUER,
    "authorization_endpoint": f"{ISSUER}/authorize",
    "token_endpoint": f"{ISSUER}/oauth/token",
    "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
    "response_types_supported": ["code"],
    "subject_types_supported": ["public"],
    "id_token_signing_alg_values_supported": ["RS256"],
}

JWKS: dict[str, Any] = {"keys": [{"kty": "RSA", "kid": "k1", "use": "sig", "n": "AQAB", "e": "AQAB"}]}


class FakeResponse(io.BytesIO):
    def __init__(self, url: str, status: int, body: bytes, final_url: str | None = None) -> None:
        super().__init__(body)
        self.status = status
        self._url = final_url or url

    def geturl(self) -> str:
        return self._url


class FakeOpener:
    """Maps a URL to ``(status, body)`` or to an exception to raise; records every request."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.requests: list[Any] = []

    def open(self, request: Any, data: None = None, timeout: float = 0) -> FakeResponse:
        self.requests.append((request, timeout))
        route = self.routes.get(request.full_url)
        if route is None:
            raise urllib.error.URLError("no route in fake")
        if isinstance(route, BaseException):
            raise route
        status, body, *rest = route
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        return FakeResponse(request.full_url, status, body, rest[0] if rest else None)


def good_routes(metadata: dict[str, Any] | None = None, jwks: Any = None) -> dict[str, Any]:
    return {
        f"{ISSUER}/.well-known/openid-configuration": (200, metadata if metadata is not None else METADATA),
        METADATA["jwks_uri"]: (200, jwks if jwks is not None else JWKS),
    }
