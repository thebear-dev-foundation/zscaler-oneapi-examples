#!/usr/bin/env bash
# List all ZIA Cloud Firewall filtering rules.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOKEN=$("$ROOT/scripts/get-token.sh")
curl -s "${ZS_API_BASE_URL:-https://api.zsapi.net}/zia/api/v1/firewallFilteringRules" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {id, name, order, state, action}'
