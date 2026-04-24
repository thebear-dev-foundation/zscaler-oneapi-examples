
# Zscaler API — Troubleshooting Commands

> **Classification: PUBLIC** — Safe for customer sharing

Quick reference for diagnosing and fixing common Zscaler OneAPI issues. All commands require a valid `ZS_TOKEN` (see [01-getting-started.md](01-getting-started.md)).

---

## Authentication

### Get a token

```bash
export ZS_TOKEN=$(curl -s -X POST "https://${ZS_VANITY_DOMAIN}/oauth2/v1/token" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${ZS_CLIENT_ID}" \
  --data-urlencode "client_secret=${ZS_CLIENT_SECRET}" \
  --data-urlencode "audience=https://api.zscaler.com" | jq -r '.access_token')
```

### Verify token is valid

```bash
curl -s -o /dev/null -w '%{http_code}' "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}"
# 200 = valid, 401 = expired
```

---

## CC Forwarding Rules

### List all rules

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, state, forwardMethod, order}'
```

### Show east-west rules with EC groups

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("East-West")) | {name, state, forwardMethod, ecGroups: [.ecGroups[].name], srcIps, destAddresses}'
```

### Show ingress rule with destinations

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("Inbound")) | {name, state, forwardMethod, locations: [.locations[].name], destAddresses}'
```

### Get a specific rule by ID

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Add CC groups to an existing east-west rule

```bash
RULE=$(curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}")

UPDATED=$(echo "$RULE" | jq '.ecGroups += [{"id": <GROUP_ID>, "name": "<GROUP_NAME>"}]')

curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$UPDATED" | jq '{name, ecGroups: [.ecGroups[].name]}'
```

---

## EC Groups (Cloud Connector Groups)

### List all EC groups

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name}'
```

### Check CC VM health in an EC group

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup/<GROUP_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '{name, ecVMs: [.ecVMs[]? | {name, publicIp, privateIp, state}]}'
```

**Note:** ZTGW-managed CCs return null for publicIp/privateIp/state. Standalone CCs may also return null — check the portal for actual status.

### Find CC groups matching a VPC ID

```bash
SEC_VPC="vpc-xxxxxxxxx"
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq --arg vpc "$SEC_VPC" \
  '[.[] | select(.name | test($vpc)) | {id, name}]'
```

---

## Locations (ZTGW Locations)

### List all locations

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/location" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name}'
```

### Find Mumbai location

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/location" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("mumbai";"i")) | {id, name}'
```

---

## Activation

### Check activation status

```bash
curl -s "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .
```

### Activate CC changes (PUT, not POST)

```bash
curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"orgEditStatus":"EDITS_PRESENT"}'
```

### Activate ZIA changes (POST, not PUT)

```bash
curl -s -X POST "https://api.zsapi.net/zia/api/v1/status/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"ACTIVE"}'
```

---

## ZIA Firewall Rules

### List all firewall rules

```bash
curl -s "https://api.zsapi.net/zia/api/v1/firewallFilteringRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, order, state, action}'
```

### Toggle a firewall rule (enable/disable)

```bash
RULE=$(curl -s "https://api.zsapi.net/zia/api/v1/firewallFilteringRules/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}")

UPDATED=$(echo "$RULE" | jq '.state = "DISABLED"')  # or "ENABLED"

curl -s -X PUT "https://api.zsapi.net/zia/api/v1/firewallFilteringRules/<RULE_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$UPDATED" | jq '{name, state}'

# Don't forget to activate ZIA changes
curl -s -X POST "https://api.zsapi.net/zia/api/v1/status/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"status":"ACTIVE"}'
```

---

## ZIA SSL Inspection Rules

### List SSL rules

```bash
curl -s "https://api.zsapi.net/zia/api/v1/sslInspectionRules" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | {id, name, order, state, action: .action.type}'
```

---

## AWS Infrastructure Checks

### GWLB target health (standalone CC only)

```bash
# Find target group ARN
TG_ARN=$(aws elbv2 describe-target-groups --names zscc-targets \
  --region <region> --query 'TargetGroups[0].TargetGroupArn' --output text)

# Check health
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" --region <region>
```

### GWLBe endpoint status

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-endpoint-type,Values=GatewayLoadBalancer" \
  --region <region> \
  --query 'VpcEndpoints[].[VpcEndpointId,State,ServiceName]' \
  --output table
```

### GWLBe creation timestamp

```bash
aws ec2 describe-vpc-endpoints \
  --filters "Name=vpc-endpoint-type,Values=GatewayLoadBalancer" \
  --region <region> \
  --query 'VpcEndpoints[0].CreationTimestamp' \
  --output text
```

### AZ mapping (physical vs logical)

```bash
aws ec2 describe-availability-zones --region <region> \
  --query 'AvailabilityZones[].[ZoneName, ZoneId]' --output table
```

### VPCE supported AZs

```bash
aws ec2 describe-vpc-endpoint-services \
  --service-names <vpce-svc-name> --region <region> \
  --query 'ServiceDetails[0].AvailabilityZones'
```

### EIP quota

```bash
# Check
aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-0263D0A3 \
  --region <region> --query 'Quota.Value'

# Increase
aws service-quotas request-service-quota-increase \
  --service-code ec2 --quota-code L-0263D0A3 \
  --desired-value 10 --region <region>
```

### VPC flow logs — check if enabled

```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=<vpc-id>" \
  --region <region> \
  --query 'FlowLogs[].[FlowLogId,FlowLogStatus,LogGroupName]' \
  --output table
```

---

## Common Troubleshooting Scenarios

### Token expired mid-workflow

```bash
# Symptom: jq parse errors, "Retrieved 1 forwarding rules"
# Fix: refresh token
export ZS_TOKEN=$(curl -s -X POST "https://${ZS_VANITY_DOMAIN}/oauth2/v1/token" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${ZS_CLIENT_ID}" \
  --data-urlencode "client_secret=${ZS_CLIENT_SECRET}" \
  --data-urlencode "audience=https://api.zscaler.com" | jq -r '.access_token')
```

### Rules updated but traffic not flowing

```bash
# 1. Check activation
curl -s "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq .

# 2. Force re-activate
curl -s -X PUT "https://api.zsapi.net/ztw/api/v1/ecAdminActivateStatus/activate" \
  -H "Authorization: Bearer ${ZS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"orgEditStatus":"EDITS_PRESENT"}'

# 3. Wait 30-60 seconds, then test
# test connectivity from your client
```

### Rules have wrong EC groups

```bash
# Check what groups are on the east-west rules
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("East-West")) | {name, ecGroups: [.ecGroups[].name]}'

# Fix: re-run with auto-discovery
# re-run your rule-creation script
```

### CC registered but not in forwarding rules

```bash
# List all CC groups
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("^zs-cc")) | {id, name}'

# Check if they're in the rules
curl -s "https://api.zsapi.net/ztw/api/v1/ecRules/ecRdr" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.[] | select(.name | test("East-West")) | .ecGroups[].name'
```

### ZTGW shows healthy but CC VMs show null in API

```bash
# This is expected for ZTGW-managed CCs — the ecgroup API doesn't expose VM details
# Check the Zscaler admin portal instead: Administration → Cloud Connector → Groups
curl -s "https://api.zsapi.net/ztw/api/v1/ecgroup/<GROUP_ID>" \
  -H "Authorization: Bearer ${ZS_TOKEN}" | jq '.ecVMs[]?'
```

---

## Quick Reference

| Action | API | Method |
|--------|-----|--------|
| List CC rules | `/ztw/api/v1/ecRules/ecRdr` | GET |
| Update CC rule | `/ztw/api/v1/ecRules/ecRdr/<id>` | PUT |
| Create CC rule | `/ztw/api/v1/ecRules/ecRdr` | POST |
| List EC groups | `/ztw/api/v1/ecgroup` | GET |
| List locations | `/ztw/api/v1/location` | GET |
| CC activation status | `/ztw/api/v1/ecAdminActivateStatus` | GET |
| CC activate | `/ztw/api/v1/ecAdminActivateStatus/activate` | **PUT** |
| ZIA firewall rules | `/zia/api/v1/firewallFilteringRules` | GET |
| ZIA activate | `/zia/api/v1/status/activate` | **POST** |
| ZIA SSL rules | `/zia/api/v1/sslInspectionRules` | GET |

**Key gotcha:** CC activation uses PUT, ZIA activation uses POST — different methods for different services.
