
# Zscaler OneAPI — Tested Command Reference

> **Classification: PUBLIC** — Safe for customer sharing
> Tested and validated commands for managing CC forwarding rules, ZIA policies, and CC groups via the Zscaler OneAPI.

---

## Authentication

### Get a Bearer Token
```bash
curl -s -X POST "https://${ZS_VANITY_DOMAIN}/oauth2/v1/token" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${ZS_CLIENT_ID}" \
  --data-urlencode "client_secret=${ZS_CLIENT_SECRET}" \
  --data-urlencode "audience=https://api.zscaler.com" | jq .
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3599
}
```

### Export the Token
```bash
export ZS_TOKEN="<paste access_token>"
```

> **Important:** The vanity domain is `z-<orgid>.zslogin.net` — **without** `-admin`. The `-admin` variant is the portal UI, not the token endpoint.

> **Important:** Use `--data-urlencode` (not `-d`) if your client secret contains special characters like `!@#`.

> **Token lifetime:** Default 3599 seconds (~60 min). Re-authenticate when expired.

### Auth gotchas
- Vanity domain is `z-<orgid>.zslogin.net` — the `-admin` variant is the portal UI, not the token endpoint
- Use `--data-urlencode` (not `-d`) — prevents special chars in the secret from breaking
- Token can be extended to 300 min via ZIdentity admin portal

---

## Forwarding Rules

### List All Forwarding Rules
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### List Rule Names Only
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[].name'
```

### List Rules with IDs and State
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, state, forwardMethod}'
```

### Get a Specific Rule by ID
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Read destAddresses from a Rule
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.destAddresses'
```

### Read destIpGroups from a Rule
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.destIpGroups'
```

### Update a Rule (PUT)
```bash
# Step 1: GET the current rule
RULE=$(curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}")

# Step 2: Modify destAddresses (merge with jq)
UPDATED=$(echo "$RULE" | jq '.destAddresses = ["1.2.3.4", "5.6.7.8", "10.0.0.1"]')

# Step 3: PUT the updated rule
curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$UPDATED" | jq .
```

> **Best practice:** Always GET before PUT to avoid overwriting other changes.

### Create an Ingress Rule (LOCAL_SWITCH with location)
```bash
curl -s -X POST "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow-ZTGW-Inbound",
    "type": "EC_RDR",
    "rank": 7,
    "order": 8,
    "forwardMethod": "LOCAL_SWITCH",
    "state": "ENABLED",
    "locations": [{"id": <LOCATION_ID>, "name": "<LOCATION_NAME>"}],
    "destAddresses": ["<EIP1>", "<EIP2>"],
    "destIpCategories": [],
    "resCategories": [],
    "destCountries": []
  }'
```

### Create East-West Rules (LOCAL_SWITCH with ecGroups)
```bash
# Forward: App VPC → Shared Services
curl -s -X POST "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow-East-West-Local",
    "type": "EC_RDR",
    "rank": 7,
    "order": 1,
    "forwardMethod": "LOCAL_SWITCH",
    "state": "ENABLED",
    "ecGroups": [{"id": <EC_GROUP_ID>, "name": "<EC_GROUP_NAME>"}],
    "srcIps": ["10.100.0.0/16"],
    "destAddresses": ["10.110.0.0/16"],
    "destIpCategories": [],
    "resCategories": [],
    "destCountries": []
  }'

# Return: Shared Services → App VPC
curl -s -X POST "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Allow-East-West-Local-Return",
    "type": "EC_RDR",
    "rank": 7,
    "order": 2,
    "forwardMethod": "LOCAL_SWITCH",
    "state": "ENABLED",
    "ecGroups": [{"id": <EC_GROUP_ID>, "name": "<EC_GROUP_NAME>"}],
    "srcIps": ["10.110.0.0/16"],
    "destAddresses": ["10.100.0.0/16"],
    "destIpCategories": [],
    "resCategories": [],
    "destCountries": []
  }'
```

> **Required fields:** `type: "EC_RDR"`, `rank: 7` — API rejects without them.
> **LOCAL_SWITCH** requires either `locations` (ingress) or `ecGroups` (east-west).

---

## Activation

Changes to forwarding rules are **not live** until activated. Always activate after creating or updating rules.

### Check Activation Status
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

Response when changes are pending:
```json
{
  "orgEditStatus": "EDITS_PRESENT",
  "orgLastActivateStatus": "CAC_ACTV_UI"
}
```

### Activate Changes (PUT, not POST)
```bash
curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"orgEditStatus":"EDITS_PRESENT"}'
```

Response on success:
```json
{
  "adminActivateStatus": "ADM_ACTV_DONE"
}
```

> **Important:** The activate endpoint is `PUT`, not `POST`. POST returns 405 Method Not Allowed.

> **Propagation time:** Allow 30-60 seconds after `ADM_ACTV_DONE` for changes to reach Cloud Connectors in your region.

### Verify Activation Completed
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

When fully activated, `orgEditStatus` will no longer show `EDITS_PRESENT`.

---

## Cloud Connector Groups

### List All EC Groups
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### List Group Names and IDs
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, platform, deployType}'
```

### Get a Specific EC Group
```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup/<GROUP_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

---

## Validation Workflow

Complete end-to-end validation after deploying infrastructure:

```bash
# 1. Authenticate
curl -s -X POST "https://${ZS_VANITY_DOMAIN}/oauth2/v1/token" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${ZS_CLIENT_ID}" \
  --data-urlencode "client_secret=${ZS_CLIENT_SECRET}" \
  --data-urlencode "audience=https://api.zscaler.com" | jq -r '.access_token'
# → export ZS_TOKEN="<token>"

# 2. Check current forwarding rules
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, state, destAddresses}'

# 3. Verify EIPs are in the rule
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.destAddresses'

# 4. Check if activation is needed
curl -s "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .

# 5. Activate if EDITS_PRESENT
curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"orgEditStatus":"EDITS_PRESENT"}'

# 6. Wait for propagation
sleep 30

# 7. Test HTTP to EIPs
curl -v --max-time 10 http://<PROD_EIP>/
curl -v --max-time 10 http://<NONPROD_EIP>/
curl -v --max-time 10 http://<DEV_EIP>/
```

---

## ZIA API — All Available Endpoints

Discovered endpoints under `https://api.zsapi.net/zia/api/v1/`:

### Security Policies

| Endpoint | GET | POST | PUT | DELETE | Description |
|----------|-----|------|-----|--------|-------------|
| `/firewallFilteringRules` | List | Create | `/{ruleId}` | `/{ruleId}` | Cloud Firewall rules |
| `/firewallFilteringRules/count` | Count | — | — | — | Rule count |
| `/urlFilteringRules` | List | Create | `/{ruleId}` | `/{ruleId}` | URL Filtering rules |
| `/firewallDnsRules` | List | Create | `/{ruleId}` | `/{ruleId}` | DNS Firewall rules |
| `/firewallIpsRules` | List | — | — | — | IPS rules |
| `/dlpDictionaries` | List | — | — | — | DLP dictionaries |
| `/dlpEngines` | List | — | — | — | DLP engines |
| `/urlCategories` | List | — | — | — | URL categories |
| `/urlLookup` | — | POST | — | — | URL category lookup (POST only) |

### Network Services & Applications

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/networkServices` | GET | Network service definitions (SSH, HTTP, etc.) |
| `/networkServiceGroups` | GET | Network service groups |
| `/networkApplications` | GET, GET `/{appId}` | Network application definitions |
| `/networkApplicationGroups` | GET | Network application groups |
| `/workloadGroups` | GET | Workload group definitions |

### IP Groups

| Endpoint | GET | POST | PUT | DELETE | Description |
|----------|-----|------|-----|--------|-------------|
| `/ipSourceGroups` | List | Create | `/{id}` | `/{id}` | Source IP groups |
| `/ipDestinationGroups` | List | Create | `/{ipGroupId}` | `/{ipGroupId}` | Destination IP groups |
| `/ipDestinationGroups/lite` | List (IDs+names only) | — | — | — | Lightweight listing |

### Identity & Access

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/users` | GET | ZIA users |
| `/departments` | GET | Departments |
| `/groups` | GET | User groups |
| `/locations` | GET | Locations |
| `/adminUsers` | GET | Admin users |
| `/adminRoles` | GET | Admin roles |
| `/deviceGroups` | GET | Device groups |

### System

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/status` | GET | ZIA service status |
| `/status/activate` | POST | Activate ZIA config changes |

---

## ZIA Cloud Firewall Rules

### List All Firewall Rules
```bash
curl -s "https://api.zsapi.net/zia/api/v1/firewallFilteringRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, order, state, action}'
```

### Get Rule Count
```bash
curl -s "https://api.zsapi.net/zia/api/v1/firewallFilteringRules/count" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Get Rule by ID
```bash
curl -s "https://api.zsapi.net/zia/api/v1/firewallFilteringRules/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Create / Update / Delete Firewall Rule
| Method | Endpoint |
|--------|----------|
| `POST` | `/zia/api/v1/firewallFilteringRules` |
| `PUT` | `/zia/api/v1/firewallFilteringRules/{ruleId}` |
| `DELETE` | `/zia/api/v1/firewallFilteringRules/{ruleId}` |

### ZIA Activation (required after changes)
```bash
curl -s -X POST "https://api.zsapi.net/zia/api/v1/status/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"ACTIVE"}'
```

---

## ZIA URL Filtering Rules

### List All URL Filtering Rules
```bash
curl -s "https://api.zsapi.net/zia/api/v1/urlFilteringRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, order, state, action}'
```

---

## ZIA IP Destination Groups

| Method | Endpoint |
|--------|----------|
| `GET` | `/zia/api/v1/ipDestinationGroups` |
| `GET` | `/zia/api/v1/ipDestinationGroups/{ipGroupId}` |
| `POST` | `/zia/api/v1/ipDestinationGroups` |
| `PUT` | `/zia/api/v1/ipDestinationGroups/{ipGroupId}` |
| `DELETE` | `/zia/api/v1/ipDestinationGroups/{ipGroupId}` |

### List All IP Destination Groups
```bash
curl -s "https://api.zsapi.net/zia/api/v1/ipDestinationGroups" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name}'
```

---

## ZIA Network Applications

| Method | Endpoint |
|--------|----------|
| `GET` | `/zia/api/v1/networkApplications` |
| `GET` | `/zia/api/v1/networkApplications/{appId}` |

### List Network Applications
```bash
curl -s "https://api.zsapi.net/zia/api/v1/networkApplications" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[].name' | head -20
```

---

## ZIA SSL Inspection Rules (tested & validated)

| Method | Endpoint |
|--------|----------|
| `GET` | `/zia/api/v1/sslInspectionRules` |
| `GET` | `/zia/api/v1/sslInspectionRules/{ruleId}` |
| `POST` | `/zia/api/v1/sslInspectionRules` |
| `PUT` | `/zia/api/v1/sslInspectionRules/{ruleId}` |
| `DELETE` | `/zia/api/v1/sslInspectionRules/{ruleId}` |

### List All SSL Rules
```bash
curl -s "https://api.zsapi.net/zia/api/v1/sslInspectionRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, order, state, action: .action.type}'
```

### Get Rule by ID
```bash
curl -s "https://api.zsapi.net/zia/api/v1/sslInspectionRules/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Create a DO_NOT_DECRYPT Bypass Rule (tested & validated)
```bash
curl -sL -X POST "https://api.zsapi.net/zia/api/v1/sslInspectionRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "name": "Bypass_SSL_ZTGW_Lab",
    "order": 1,
    "rank": 7,
    "locations": [{"id": <LOCATION_ID>}],
    "roadWarriorForKerberos": false,
    "action": {
      "type": "DO_NOT_DECRYPT",
      "doNotDecryptSubActions": {
        "bypassOtherPolicies": false,
        "serverCertificates": "ALLOW",
        "ocspCheck": false,
        "minTLSVersion": "SERVER_TLS_1_0",
        "blockSslTrafficWithNoSniEnabled": false
      },
      "showEUN": false,
      "showEUNATP": false,
      "overrideDefaultCertificate": false
    },
    "state": "ENABLED",
    "defaultRule": false
  }'
```

> **Critical gotcha:** Do NOT include empty arrays for `platforms`, `urlCategories`, `cloudApplications` — API returns `"Empty array is not allowed"`. Only send fields you need.

> **Key finding:** This bypass rule fixes `pip install` failing with `SSL: CERTIFICATE_VERIFY_FAILED` on workloads whose traffic goes through ZIA SSL inspection. Without it, ZIA's `All Categories` DECRYPT rule intercepts the PyPI HTTPS connection and pip rejects the Zscaler-issued certificate.

### Delete SSL Rule
```bash
curl -sL -X DELETE "https://api.zsapi.net/zia/api/v1/sslInspectionRules/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}"
```

### Activate After SSL Changes
```bash
curl -s -X POST "https://api.zsapi.net/zia/api/v1/status/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"ACTIVE"}'
```

---

## ZIA DNS / IPS Rules

| API | Endpoint |
|-----|----------|
| DNS Rules | `/zia/api/v1/firewallDnsRules` |
| IPS Rules | `/zia/api/v1/firewallIpsRules` |
| Network Services | `/zia/api/v1/networkServices` |

---

## Endpoint Discovery

Scan for all working ZIA endpoints:

```bash
for ep in firewallFilteringRules urlFilteringRules firewallDnsRules firewallIpsRules \
  networkServices networkServiceGroups networkApplications networkApplicationGroups \
  ipSourceGroups ipDestinationGroups dlpDictionaries dlpEngines urlCategories \
  users departments groups locations adminUsers adminRoles status workloadGroups deviceGroups; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://api.zsapi.net/zia/api/v1/$ep" \
    -H "Authorization: Bearer ${ZS_TOKEN}")
  [[ "$CODE" != "404" ]] && echo "$CODE  $ep"
done
```

---

## Automated Scripts

| Command | What it does |
|---------|-------------|
| `make ew-open` | Enable east-west LOCAL_SWITCH rules |
| `make ew-close` | Disable east-west LOCAL_SWITCH rules |
| `make ew-status` | Check east-west rule status |
| `make rules-create` | Create all forwarding rules |
| `make zia-drop-on` | Enable ZIA firewall drop rule |
| `make zia-drop-off` | Disable ZIA firewall drop rule |
| `make zia-show` | Show ZIA firewall rules |
| `./scripts/ztgw-manage-rules.sh --show` | Show all ZTGW rules (detailed) |
| `./scripts/ztgw-manage-rules.sh --east-west-only` | Create east-west rules only |
| `./scripts/ztgw-manage-rules.sh --ingress-only` | Create ingress rule only |

---

## Gotchas

| Issue | Cause | Fix |
|-------|-------|-----|
| Token request returns empty | Using `-admin` vanity domain | Use `z-<orgid>.zslogin.net` without `-admin` |
| Token request returns 302 | curl not following redirect with POST body | Use `--data-urlencode` instead of `-d` |
| CC activate returns 405 | Using POST | Use `PUT` with body `{"orgEditStatus":"EDITS_PRESENT"}` |
| ZIA activate returns 405 | Using PUT | Use `POST` with body `{"status":"ACTIVE"}` |
| Rule create fails "rank required" | Missing `rank` and `type` fields | Include `"type":"EC_RDR"`, `"rank":7` |
| Rule create fails "order not allowed" | Order position taken by another rule | Change the `order` value |
| Same IPs in src and dst | CC API rejects identical CIDRs | Use specific VPC CIDRs, not RFC1918 |
| LOCAL_SWITCH requires location or ecGroup | API validation | Add `locations` (ingress) or `ecGroups` (east-west) |
| HTTP hangs from workstation | Traffic routed through ZIA instead of ZTGW | Test from client VPC; allow 30-60s after activation |
| HTTPS hangs | ZTE SSL inspection + self-signed nginx cert | Known limitation (BUG-234246) — test with HTTP port 80 |
| `destAddresses` set but traffic doesn't flow | Config not activated | Check `ecAdminActivateStatus` and activate |
| Rule update works but EIPs gone on next check | PUT overwrote other fields | Always GET full rule first, modify, then PUT back |
| SSL rule POST returns "Empty array is not allowed" | Empty arrays like `platforms: []` | Remove the field entirely — don't send empty arrays |
| pip install fails with SSL_CERTIFICATE_VERIFY_FAILED | ZIA SSL inspection intercepts PyPI HTTPS | Create `DO_NOT_DECRYPT` bypass for ZTGW location |
| Up to 10 min propagation | Normal for CC policy updates | Wait, or use ZTGW config refresh |
