# rakomi

OpenID Connect discovery for [Rakomi](https://rakomi.com) issuers. Python 3.10 or later, no
dependencies outside the standard library.

```sh
pip install rakomi
```

```python
from rakomi import DiscoveryError, discover

try:
    result = discover("https://api.rakomi.com", timeout=5.0)
except DiscoveryError as exc:
    raise SystemExit(f"discovery failed: {exc}")

print(result.issuer)
print(result.metadata["authorization_endpoint"])
print(result.jwks["keys"])
```

`discover` fetches `<issuer>/.well-known/openid-configuration`, then the JSON Web Key Set at its
`jwks_uri`, and returns both as a `Discovery` (`metadata`, `jwks`).

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
