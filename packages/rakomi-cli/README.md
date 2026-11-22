# rakomi-cli

Command-line tools for [Rakomi](https://rakomi.com). Python 3.10 or later.

```sh
pipx install rakomi-cli
rakomi-discover https://api.rakomi.com
```

`rakomi-discover <issuer>` fetches the issuer's OpenID Connect metadata and its JWKS, checks them, and
prints the metadata as JSON. It exits with 1 and a message on stderr when discovery is refused.

Options: `--timeout SECONDS` (default 10), `--version`.

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
