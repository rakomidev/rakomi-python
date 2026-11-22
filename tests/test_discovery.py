# SPDX-License-Identifier: MIT
from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from fake import ISSUER, JWKS, METADATA, FakeOpener, good_routes
from rakomi import Discovery, DiscoveryError, discover
from rakomi.discovery import MAX_DOCUMENT_BYTES, _RefuseRedirects, _default_opener


def test_discover_returns_metadata_and_jwks() -> None:
    opener = FakeOpener(good_routes())
    result = discover(ISSUER, opener=opener, timeout=3.0)
    assert isinstance(result, Discovery)
    assert result.issuer == ISSUER
    assert result.jwks_uri == METADATA["jwks_uri"]
    assert result.jwks == JWKS
    urls = [request.full_url for request, _ in opener.requests]
    assert urls == [f"{ISSUER}/.well-known/openid-configuration", METADATA["jwks_uri"]]
    assert all(timeout == 3.0 for _, timeout in opener.requests)


def test_issuer_with_path_keeps_the_path() -> None:
    issuer = f"{ISSUER}/tenant"
    metadata = dict(METADATA, issuer=issuer)
    opener = FakeOpener({f"{issuer}/.well-known/openid-configuration": (200, metadata), METADATA["jwks_uri"]: (200, JWKS)})
    assert discover(issuer, opener=opener).issuer == issuer


@pytest.mark.parametrize(
    "issuer",
    ["http://issuer.example", "ftp://issuer.example", "issuer.example", "", "https://", "https://u:p@issuer.example",
     "https://issuer.example?x=1", "https://issuer.example#f"],
)
def test_refuses_bad_issuer_without_any_request(issuer: str) -> None:
    opener = FakeOpener(good_routes())
    with pytest.raises(DiscoveryError):
        discover(issuer, opener=opener)
    assert opener.requests == []


def test_refuses_issuer_mismatch() -> None:
    opener = FakeOpener(good_routes(dict(METADATA, issuer="https://other.example")))
    with pytest.raises(DiscoveryError, match="expected"):
        discover(ISSUER, opener=opener)
    assert len(opener.requests) == 1


def test_trailing_slash_issuer_must_match_exactly() -> None:
    opener = FakeOpener(good_routes())
    with pytest.raises(DiscoveryError, match="expected"):
        discover(ISSUER + "/", opener=opener)


@pytest.mark.parametrize("field", ["issuer", "authorization_endpoint", "token_endpoint", "jwks_uri",
                                   "response_types_supported", "subject_types_supported",
                                   "id_token_signing_alg_values_supported"])
def test_refuses_missing_required_field(field: str) -> None:
    metadata = {k: v for k, v in METADATA.items() if k != field}
    with pytest.raises(DiscoveryError, match="missing"):
        discover(ISSUER, opener=FakeOpener(good_routes(metadata)))


@pytest.mark.parametrize("field", ["authorization_endpoint", "token_endpoint", "jwks_uri"])
def test_refuses_plain_http_endpoint(field: str) -> None:
    metadata = dict(METADATA, **{field: "http://issuer.example/x"})
    opener = FakeOpener(good_routes(metadata))
    with pytest.raises(DiscoveryError, match="https"):
        discover(ISSUER, opener=opener)
    assert len(opener.requests) == 1


@pytest.mark.parametrize("value", [[], "code", [1], None])
def test_refuses_bad_supported_list(value: object) -> None:
    metadata = dict(METADATA, response_types_supported=value)
    with pytest.raises(DiscoveryError, match="list"):
        discover(ISSUER, opener=FakeOpener(good_routes(metadata)))


@pytest.mark.parametrize("jwks", [{}, {"keys": "x"}, {"keys": [1]}, [1]])
def test_refuses_bad_jwks(jwks: object) -> None:
    with pytest.raises(DiscoveryError):
        discover(ISSUER, opener=FakeOpener(good_routes(jwks=jwks)))


@pytest.mark.parametrize("body", [b"not json", b"\xff\xfe", b"[1, 2]", b'"s"'])
def test_refuses_non_object_metadata(body: bytes) -> None:
    routes = good_routes()
    routes[f"{ISSUER}/.well-known/openid-configuration"] = (200, body)
    with pytest.raises(DiscoveryError, match="JSON"):
        discover(ISSUER, opener=FakeOpener(routes))


def test_refuses_oversized_document() -> None:
    routes = good_routes()
    routes[f"{ISSUER}/.well-known/openid-configuration"] = (200, b" " * (MAX_DOCUMENT_BYTES + 1))
    with pytest.raises(DiscoveryError, match="more than"):
        discover(ISSUER, opener=FakeOpener(routes))


def test_refuses_non_200_status() -> None:
    routes = good_routes()
    routes[f"{ISSUER}/.well-known/openid-configuration"] = (204, b"{}")
    with pytest.raises(DiscoveryError, match="HTTP 204"):
        discover(ISSUER, opener=FakeOpener(routes))


def test_refuses_answer_from_another_url() -> None:
    routes = good_routes()
    routes[f"{ISSUER}/.well-known/openid-configuration"] = (200, METADATA, "http://issuer.example/x")
    with pytest.raises(DiscoveryError, match="another URL"):
        discover(ISSUER, opener=FakeOpener(routes))


@pytest.mark.parametrize("exc", [
    urllib.error.HTTPError(f"{ISSUER}/.well-known/openid-configuration", 404, "nf", {}, None),  # type: ignore[arg-type]
    urllib.error.URLError("down"),
    TimeoutError("timed out"),
])
def test_transport_errors_become_discovery_errors(exc: BaseException) -> None:
    routes = good_routes()
    routes[f"{ISSUER}/.well-known/openid-configuration"] = exc
    with pytest.raises(DiscoveryError):
        discover(ISSUER, opener=FakeOpener(routes))


def test_refuses_non_positive_timeout() -> None:
    with pytest.raises(DiscoveryError, match="timeout"):
        discover(ISSUER, opener=FakeOpener(good_routes()), timeout=0)


def test_default_opener_refuses_redirects() -> None:
    opener = _default_opener()
    assert any(isinstance(h, _RefuseRedirects) for h in opener.handlers)
    assert not any(type(h) is urllib.request.HTTPRedirectHandler for h in opener.handlers)
    request = urllib.request.Request(f"{ISSUER}/.well-known/openid-configuration")
    with pytest.raises(DiscoveryError, match="redirect"):
        _RefuseRedirects().redirect_request(request, None, 302, "Found", {}, "http://evil.example/")
