# SPDX-License-Identifier: MIT
"""OpenID Connect discovery over HTTPS, using only the standard library."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

__all__ = ["Discovery", "DiscoveryError", "discover", "DEFAULT_TIMEOUT", "MAX_DOCUMENT_BYTES"]

DEFAULT_TIMEOUT = 10.0
"""Seconds allowed for each HTTPS request."""

MAX_DOCUMENT_BYTES = 1024 * 1024
"""Largest metadata or JWKS document accepted, in bytes."""

WELL_KNOWN_PATH = "/.well-known/openid-configuration"

REQUIRED_METADATA = (
    "issuer",
    "authorization_endpoint",
    "token_endpoint",
    "jwks_uri",
    "response_types_supported",
    "subject_types_supported",
    "id_token_signing_alg_values_supported",
)
"""Fields the provider metadata must carry (OpenID Connect Discovery 1.0, section 3)."""


class DiscoveryError(Exception):
    """Discovery failed: the issuer, the transport or a fetched document was refused."""


class Opener(Protocol):
    """Anything with the ``open`` method of :class:`urllib.request.OpenerDirector`."""

    def open(self, fullurl: urllib.request.Request, data: None = None, timeout: float = ...) -> Any: ...


@dataclass(frozen=True)
class Discovery:
    """The provider metadata of an issuer and the JSON Web Key Set its ``jwks_uri`` serves."""

    metadata: Mapping[str, Any]
    jwks: Mapping[str, Any]

    @property
    def issuer(self) -> str:
        return str(self.metadata["issuer"])

    @property
    def jwks_uri(self) -> str:
        return str(self.metadata["jwks_uri"])


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise DiscoveryError(f"refused redirect from {req.full_url} (HTTP {code})")


def _default_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_RefuseRedirects())


def _require_https(url: str, what: str) -> urllib.parse.SplitResult:
    if not isinstance(url, str) or not url:
        raise DiscoveryError(f"{what} must be a non-empty string")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        raise DiscoveryError(f"{what} must use https: {url}")
    if not parts.hostname:
        raise DiscoveryError(f"{what} has no host: {url}")
    if parts.username is not None or parts.password is not None:
        raise DiscoveryError(f"{what} must not carry credentials")
    return parts


def _fetch_json(url: str, opener: Opener, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with opener.open(request, timeout=timeout) as response:
            status = getattr(response, "status", None)
            if status != 200:
                raise DiscoveryError(f"{url} answered HTTP {status}")
            final_url = response.geturl()
            if final_url != url:
                raise DiscoveryError(f"{url} was answered from another URL: {final_url}")
            body = response.read(MAX_DOCUMENT_BYTES + 1)
    except DiscoveryError:
        raise
    except urllib.error.HTTPError as exc:
        raise DiscoveryError(f"{url} answered HTTP {exc.code}") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise DiscoveryError(f"could not fetch {url}: {exc}") from None
    if len(body) > MAX_DOCUMENT_BYTES:
        raise DiscoveryError(f"{url} returned more than {MAX_DOCUMENT_BYTES} bytes")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DiscoveryError(f"{url} did not return valid JSON") from None
    if not isinstance(document, dict):
        raise DiscoveryError(f"{url} did not return a JSON object")
    return document


def _validate_metadata(metadata: dict[str, Any], issuer: str) -> None:
    missing = [name for name in REQUIRED_METADATA if name not in metadata]
    if missing:
        raise DiscoveryError(f"provider metadata is missing: {', '.join(missing)}")
    if metadata["issuer"] != issuer:
        raise DiscoveryError(
            f"provider metadata names issuer {metadata['issuer']!r}, expected {issuer!r}"
        )
    for name in ("authorization_endpoint", "token_endpoint", "jwks_uri"):
        _require_https(metadata[name], name)
    for name in (
        "response_types_supported",
        "subject_types_supported",
        "id_token_signing_alg_values_supported",
    ):
        value = metadata[name]
        if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
            raise DiscoveryError(f"{name} must be a non-empty list of strings")


def _validate_jwks(jwks: dict[str, Any]) -> None:
    keys = jwks.get("keys")
    if not isinstance(keys, list) or not all(isinstance(key, dict) for key in keys):
        raise DiscoveryError("JWKS must carry a 'keys' list of JSON objects")


def discover(
    issuer: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    opener: Optional[Opener] = None,
) -> Discovery:
    """Fetch and check the provider metadata of ``issuer`` and the JWKS it points at.

    ``issuer`` is the exact issuer identifier, for example ``"https://api.rakomi.com"``. Both
    documents are fetched over HTTPS only; redirects are refused. The metadata must name exactly
    ``issuer`` as its issuer and carry the fields in :data:`REQUIRED_METADATA`.

    ``opener`` replaces the default :mod:`urllib.request` opener (for a proxy or tests); it should
    refuse redirects as the default one does.

    Raises :class:`DiscoveryError` on any refusal.
    """
    parts = _require_https(issuer, "issuer")
    if parts.query or parts.fragment:
        raise DiscoveryError("issuer must not have a query or fragment")
    if timeout <= 0:
        raise DiscoveryError("timeout must be positive")
    opener = opener if opener is not None else _default_opener()

    metadata_url = issuer.rstrip("/") + WELL_KNOWN_PATH
    metadata = _fetch_json(metadata_url, opener, timeout)
    _validate_metadata(metadata, issuer)
    jwks = _fetch_json(metadata["jwks_uri"], opener, timeout)
    _validate_jwks(jwks)
    return Discovery(metadata=metadata, jwks=jwks)
