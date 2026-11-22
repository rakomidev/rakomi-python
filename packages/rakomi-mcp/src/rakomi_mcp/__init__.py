# SPDX-License-Identifier: MIT
"""Early Rakomi package for MCP integrations.

It currently provides OpenID Connect discovery of a Rakomi issuer, which an MCP client or server
needs to locate the issuer's endpoints and signing keys. It does not implement an MCP server or
client.
"""

from rakomi import Discovery, DiscoveryError, discover

__all__ = ["Discovery", "DiscoveryError", "discover", "__version__"]

__version__ = "0.1.0"
