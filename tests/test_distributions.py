# SPDX-License-Identifier: MIT
from __future__ import annotations

import json

import pytest

import rakomi
import rakomi_mcp
import rakomi_sdk
from fake import ISSUER, METADATA, FakeOpener, good_routes
from rakomi_cli import __version__ as cli_version
from rakomi_cli.discover import main


@pytest.mark.parametrize("module", [rakomi_sdk, rakomi_mcp])
def test_reexports_the_client(module: object) -> None:
    assert module.discover is rakomi.discover  # type: ignore[attr-defined]
    assert module.DiscoveryError is rakomi.DiscoveryError  # type: ignore[attr-defined]


def test_versions_agree() -> None:
    assert {rakomi.__version__, rakomi_sdk.__version__, rakomi_mcp.__version__, cli_version} == {"0.1.0"}


def test_cli_prints_metadata_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([ISSUER], opener=FakeOpener(good_routes())) == 0
    out, err = capsys.readouterr()
    assert json.loads(out) == METADATA
    assert err == ""


def test_cli_reports_refusal_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["http://issuer.example"], opener=FakeOpener(good_routes())) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert "https" in err


def test_cli_requires_issuer(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])
    assert exit_info.value.code == 2
