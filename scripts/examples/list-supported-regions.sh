#!/usr/bin/env bash
# Enumerate AWS regions Zscaler supports for Public Cloud (partner) accounts.
# Use the numeric id + enum name in POST /publicCloudInfo supportedRegions field.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TOKEN=$("$ROOT/scripts/get-token.sh")
curl -s "${ZS_API_BASE_URL:-https://api.zsapi.net}/ztw/api/v1/publicCloudInfo/supportedRegions" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.[] | {id, cloudType, name}'
