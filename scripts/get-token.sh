#!/usr/bin/env bash
# Emit a OneAPI bearer token to stdout. Reads ZS_VANITY_DOMAIN, ZS_CLIENT_ID,
# ZS_CLIENT_SECRET from the environment (source your .env first).
set -euo pipefail

: "${ZS_VANITY_DOMAIN:?ZS_VANITY_DOMAIN is unset. Source your .env.}"
: "${ZS_CLIENT_ID:?ZS_CLIENT_ID is unset. Source your .env.}"
: "${ZS_CLIENT_SECRET:?ZS_CLIENT_SECRET is unset. Source your .env.}"

curl -s -X POST "https://${ZS_VANITY_DOMAIN}/oauth2/v1/token" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${ZS_CLIENT_ID}" \
  --data-urlencode "client_secret=${ZS_CLIENT_SECRET}" \
  --data-urlencode "audience=${ZS_AUDIENCE:-https://api.zscaler.com}" \
  | jq -r '.access_token // empty'
