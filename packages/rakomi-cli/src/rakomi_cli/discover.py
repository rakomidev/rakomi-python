# SPDX-License-Identifier: MIT
"""``rakomi-discover <issuer>``: print the OpenID Connect provider metadata of an issuer."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from rakomi import DiscoveryError, discover
from rakomi.discovery import DEFAULT_TIMEOUT, Opener

from rakomi_cli import __version__


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rakomi-discover",
        description=(
            "Fetch an issuer's OpenID Connect metadata and its JWKS over HTTPS, check them, "
            "and print the metadata as JSON."
        ),
    )
    parser.add_argument("issuer", help="exact issuer identifier, e.g. https://api.rakomi.com")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"seconds allowed for each request (default {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[Sequence[str]] = None, *, opener: Optional[Opener] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = discover(args.issuer, timeout=args.timeout, opener=opener)
    except DiscoveryError as exc:
        print(f"rakomi-discover: {exc}", file=sys.stderr)
        return 1
    json.dump(dict(result.metadata), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
