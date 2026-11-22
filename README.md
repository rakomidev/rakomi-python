# rakomi-python

Python packages for [Rakomi](https://rakomi.com).

| Package | What it provides today |
|---|---|
| [`rakomi`](packages/rakomi) | `discover(issuer)`: OpenID Connect discovery of an issuer and its JWKS, standard library only |
| [`rakomi-sdk`](packages/rakomi-sdk) | The same client under the `rakomi_sdk` import name |
| [`rakomi-cli`](packages/rakomi-cli) | The `rakomi-discover <issuer>` command |
| [`rakomi-mcp`](packages/rakomi-mcp) | Early package for MCP integrations; it currently provides discovery only |

All four are at version 0.1.0 and need Python 3.10 or later.

```python
from rakomi import discover

result = discover("https://api.rakomi.com")
print(result.metadata["token_endpoint"])
print([key["kid"] for key in result.jwks["keys"]])
```

## Development

```sh
uv run --with pytest pytest
for d in packages/*; do uv build "$d" --out-dir dist; done
```

The tests use an in-memory stand-in for the HTTP layer and open no network connections.

## Security

See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).
