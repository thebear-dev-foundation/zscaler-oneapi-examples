#!/usr/bin/env bash
# List all ZTW Locations (for use in forwarding rules, SSL rules, etc.).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOKEN=$("$ROOT/scripts/get-token.sh")
curl -s "${ZS_API_BASE_URL:-https://api.zsapi.net}/ztw/api/v1/location" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {id, name}'
