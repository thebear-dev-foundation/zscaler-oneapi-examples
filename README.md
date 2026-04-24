# zscaler-oneapi-examples

Curated, hand-tested reference for building against the **Zscaler OneAPI** — authentication, common request/response shapes, gotchas, and a read-only discovery probe.

Scope: **Cloud & Branch Connector (`/ztw/api/v1`)** + **ZIA (`/zia/api/v1`)**. ZPA, ZDX, ZIdentity, and Client Connector are covered in the getting-started authentication guide but not in command-reference depth (yet).

## Who this is for

- Cloud engineers building Zscaler integrations for AWS / Azure / GCP landing zones.
- Security engineers automating ZIA firewall / URL filtering / SSL inspection policy.
- SOC / platform teams writing operational runbooks against Cloud Connector forwarding rules and activation.
- Anyone evaluating Zscaler automation before committing to a full SDK dependency.

## What's inside

```
zscaler-oneapi-examples/
├── README.md                          — this file
├── LICENSE                            — Apache 2.0
├── CHANGELOG.md
├── .env.example                       — OneAPI credential template
├── docs/
│   ├── 01-getting-started.md          — Auth (Client Secret + JWKS + certs), base URLs, first calls
│   ├── 02-command-reference.md        — Full CC + ZIA command reference (curl examples, tested)
│   └── 03-troubleshooting.md          — Gotchas, error codes, activation quirks, common scenarios
└── scripts/
    ├── get-token.sh                   — One-liner: emit a valid bearer token from .env
    ├── probe-endpoints.py             — Read-only resource-shape discovery across CC + ZIA
    └── examples/
        ├── list-forwarding-rules.sh
        ├── list-zia-firewall-rules.sh
        ├── list-ec-groups.sh
        ├── list-locations.sh
        └── list-supported-regions.sh
```

## Quickstart

```bash
# 1. Configure creds
cp .env.example .env
# edit .env — populate ZS_VANITY_DOMAIN, ZS_CLIENT_ID, ZS_CLIENT_SECRET

# 2. Get a token (prints bearer to stdout)
source .env
TOKEN=$(./scripts/get-token.sh)
echo $TOKEN | head -c 32; echo ...

# 3. Try an example call
./scripts/examples/list-forwarding-rules.sh

# 4. Discover what your tenant exposes (read-only, safe)
./scripts/probe-endpoints.py
```

## Key things to know before you start

1. **OAuth2 Client Credentials flow via ZIdentity** — not a long-lived API key. Token TTL defaults to 3599 seconds (~60 min).
2. **Vanity domain is `z-<orgid>.zslogin.net`** — NOT `-admin` (which is the portal UI, not the token endpoint).
3. **Rate limit: 1 request / second** on ZIA + ZTW APIs. Always serialize; add a 1.5-second gap between calls if running scripts.
4. **Activation required after most changes:**
   - ZIA: `POST /zia/api/v1/status/activate` with `{"status":"ACTIVE"}`
   - CC:  `PUT /ztw/api/v1/ecAdminActivateStatus/activate` with `{"orgEditStatus":"EDITS_PRESENT"}`
   - Note: **different HTTP verbs** — POST for ZIA, PUT for CC.
5. **Always GET before PUT** — PUT requires the full resource; partial PUTs overwrite unspecified fields with nulls.
6. **SFTP/SSH is not TLS** — SSL Inspection rules don't apply to SSH-based SFTP; use Firewall Filtering + Network Service rules instead.

See [docs/01-getting-started.md](docs/01-getting-started.md) for the full overview and [docs/02-command-reference.md](docs/02-command-reference.md) for the tested command library.

## Related modules

- [`ztcloud-aws-lambda-egress`](https://github.com/thebear-dev-foundation/ztcloud-aws-lambda-egress) — apply these OneAPI patterns to steer AWS Lambda egress through Zscaler with a subnet-based policy identifier.
- [`ztcloud-aws-account-autolink`](https://github.com/thebear-dev-foundation/ztcloud-aws-account-autolink) — real-time AWS account onboarding into the Connector Portal using these OneAPI endpoints.

## Contributing

Welcome. Scope guideline: commands/examples must have been **tested against a real tenant** — no guesses. Include the exact response shape in the docs.

## License

Apache License, Version 2.0 — see [LICENSE](LICENSE).

## Disclaimer

Community reference. Zscaler provides no warranty. API shapes evolve — check the official Zscaler documentation for authoritative current definitions.
