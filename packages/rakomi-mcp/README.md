# rakomi-mcp

An early package for using [Rakomi](https://rakomi.com) with the Model Context Protocol. **Today it
provides only OpenID Connect discovery of a Rakomi issuer** — locating the issuer's endpoints and
signing keys. It does not implement an MCP server, an MCP client or MCP authorization. Python 3.10 or
later.

```sh
pip install rakomi-mcp
```

```python
from rakomi_mcp import discover

result = discover("https://api.rakomi.com")
print(result.metadata["token_endpoint"])
```

## What `discover` checks

- The issuer and every endpoint it reads use `https`; an issuer with credentials, a query or a
  fragment is refused.
- Redirects are refused.
- The metadata names exactly the issuer you passed (`"https://api.rakomi.com"` and
  `"https://api.rakomi.com/"` are different issuers).
- The metadata carries `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`,
  `response_types_supported`, `subject_types_supported` and `id_token_signing_alg_values_supported`.
- The JWKS is a JSON object with a `keys` list.
- Each request has a timeout (10 seconds by default) and each document is limited to 1 MiB.

Any refusal raises `DiscoveryError`. `discover` does not verify tokens.

## Security

Report vulnerabilities to security@rakomi.com. See
[SECURITY.md](https://github.com/rakomidev/rakomi-python/blob/main/SECURITY.md).

## License

MIT
