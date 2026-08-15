@~/.claude/CLAUDE.md

# This repo: zscaler-oneapi-examples

Curated, hand-tested reference for building against the Zscaler OneAPI — authentication, common request/response shapes, gotchas, and a read-only discovery probe. In-scope: Cloud & Branch Connector (`/ztw/api/v1`) + ZIA (`/zia/api/v1`). ZPA / ZDX / ZIdentity / Client Connector covered in the auth getting-started but not in command-reference depth (yet).

## Stack
- Markdown documentation (primary)
- Python (`scripts/` — one Python script for the discovery probe)
- Apache 2.0 licensed (per `LICENSE`)

## Structure
- `README.md`, `CHANGELOG.md`, `LICENSE`
- `docs/` — the curated OneAPI reference (auth, request/response patterns, gotchas)
- `scripts/` — read-only discovery probe (Python)

## Conventions
- Hand-tested only — every example must be verified against a live OneAPI surface before being committed.
- Read-only by design: the discovery probe never mutates tenant state.
- Apache 2.0 licensed — this is the public-facing reference; treat content as published.

## Constraints
- PUBLIC repo (Apache 2.0). Never include tenant-specific secrets, customer data, or internal-only artefacts.
- Read-only contract: any addition to `scripts/` that mutates tenant state needs a documented rationale + opt-in flag.

## Entry points
- Read `docs/` for the curated reference.
- `scripts/` for the discovery probe (run against your own tenant — read-only).
- No build / no CI — this is a reference repo.
