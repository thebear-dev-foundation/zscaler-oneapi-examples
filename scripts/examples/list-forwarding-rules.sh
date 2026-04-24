#!/usr/bin/env bash
# List all Cloud Connector forwarding rules.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOKEN=$("$ROOT/scripts/get-token.sh")
curl -s "${ZS_API_BASE_URL:-https://api.zsapi.net}/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {id, name, state, forwardMethod, order, srcIps, destAddresses}'
