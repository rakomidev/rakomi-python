# SPDX-License-Identifier: MIT
"""Rakomi SDK for Python. It currently provides OpenID Connect discovery of a Rakomi issuer."""

from rakomi import Discovery, DiscoveryError, discover

__all__ = ["Discovery", "DiscoveryError", "discover", "__version__"]

__version__ = "0.1.0"
