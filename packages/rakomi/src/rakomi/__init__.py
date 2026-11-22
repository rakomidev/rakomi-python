# SPDX-License-Identifier: MIT
"""Rakomi client for Python: OpenID Connect discovery of a Rakomi issuer."""

from rakomi.discovery import Discovery, DiscoveryError, discover

__all__ = ["Discovery", "DiscoveryError", "discover", "__version__"]

__version__ = "0.1.0"
