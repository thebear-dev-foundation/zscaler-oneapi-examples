
# Zscaler OneAPI — Getting Started Guide

> **Classification: EXTERNAL** — Safe for customer sharing
> Reference documentation for authenticating and making API calls to Zscaler services.

---

## Overview

Zscaler OneAPI provides unified programmatic access to Zscaler services with consistent API design across all products. It uses OAuth 2.0 (Client Credentials flow) via ZIdentity as the authorization server.

---

## 1. Getting Access

### Prerequisites

- Subscription to OneAPI and ZIdentity (contact your Zscaler Account team)
- API Client registered in ZIdentity with the necessary scope

### API Resources and Roles

Each Zscaler service maps to a resource in ZIdentity with role-based access:

- API Clients can be assigned **one resource per product** (read, write, or restricted)
- API Clients can be assigned **multiple resources across different products**

---

## 2. Authenticating

Authentication uses OAuth 2.0 Client Credentials flow. ZIdentity issues an access token used in all subsequent API calls.

### Token Endpoint

```
POST https://<vanity-domain>.zslogin.net/oauth2/v1/token
```

Replace `<vanity-domain>` with the domain assigned to your organization.

### Authentication Methods

| Method | Best For | Key Rotation |
|--------|----------|-------------|
| Client Secret | Testing, lab, PoC | Manual in ZIdentity |
| JWKS URL | Production automation | Automatic (seamless) |
| Certificates/Public Keys | Compliance/regulatory environments | Manual in ZIdentity |

---

### Option 1: Client Secret

```http
POST /oauth2/v1/token HTTP/1.1
Host: <vanity-domain>.zslogin.net
Content-Type: application/x-www-form-urlencoded

{
  "grant_type": "client_credentials",
  "client_id": "<Client ID>",
  "client_secret": "<Client Secret>",
  "audience": "https://api.zscaler.com"
}
```

Or using Basic authentication:

```http
POST /oauth2/v1/token HTTP/1.1
Host: <vanity-domain>.zslogin.net
Authorization: Basic <Base64(clientID:clientSecret)>
Content-Type: application/x-www-form-urlencoded

{
  "grant_type": "client_credentials",
  "audience": "https://api.zscaler.com"
}
```

### Option 2: JWKS URL (Private Key JWT)

Generate a key pair:

```bash
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

JWT signing pseudocode:

```
header    = base64url_encode({ "alg": "RS256", "typ": "JWT" })
payload   = base64url_encode({
              "iss": client_id,
              "sub": client_id,
              "aud": "https://api.zscaler.com",
              "exp": now() + 600
            })
unsigned  = header + "." + payload
signature = sign_with_private_key(unsigned, algorithm="RS256")
jwt       = unsigned + "." + base64url_encode(signature)
```

Token request with JWT assertion:

```http
POST /oauth2/v1/token HTTP/1.1
Host: <vanity-domain>.zslogin.net
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=<Client ID>
&client_assertion=<jwt>
&client_assertion_type=urn:ietf:params:oauth:client-assertion-type:jwt-bearer
&audience=https://api.zscaler.com
```

### Option 3: Certificates/Public Keys

Upload the client's public key (`.pem`) or X.509 certificate directly into ZIdentity. The client signs JWTs with its private key and ZIdentity validates against the uploaded public key.

### Successful Token Response

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6Ikp...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

Use the token in all subsequent API calls:

```
Authorization: Bearer <access_token>
```

---

## 3. Making API Calls

### Base URLs

| API | Base Path | Base URL |
|-----|-----------|----------|
| ZIA | `/zia/api/v1` | `https://api.zsapi.net/zia/api/v1` |
| ZPA | `/zpa/mgmtconfig/v1` | `https://api.zsapi.net/zpa/mgmtconfig/v1` |
| ZPA v2 | `/zpa/mgmtconfig/v2` | `https://api.zsapi.net/zpa/mgmtconfig/v2` |
| ZDX | `/zdx/v1` | `https://api.zsapi.net/zdx/v1` |
| ZIdentity | `/ziam/admin/api/v1` | `https://api.zsapi.net/ziam/admin/api/v1` |
| Client Connector | `/zcc/papi/public/v1` | `https://api.zsapi.net/zcc/papi/public/v1` |
| **Cloud & Branch Connector** | **`/ztw/api/v1`** | **`https://api.zsapi.net/ztw/api/v1`** |
| Business Insights | `/bi/api/v1` | `https://api.zsapi.net/bi/api/v1` |

> Beta endpoint available at `api.beta.zsapi.net` with the same base paths.

---

## 4. API Examples

### ZIA — URL Lookup

```python
import requests

url = "https://api.zsapi.net/zia/api/v1/urlLookup"
payload = ["viruses.org", "facebook.com", "bbc.com"]
headers = {
  "Authorization": "Bearer <Access Token>"
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

Response:

```json
[
  {
    "url": "viruses.org",
    "urlClassifications": ["MISCELLANEOUS_OR_UNKNOWN"],
    "urlClassificationsWithSecurityAlert": []
  },
  {
    "url": "facebook.com",
    "urlClassifications": ["SOCIAL_NETWORKING"],
    "urlClassificationsWithSecurityAlert": []
  }
]
```

### Cloud & Branch Connector — List EC Groups

```python
import requests

url = "https://api.zsapi.net/ztw/api/v1/ecgroup"
headers = {
  "Authorization": "Bearer <Access Token>"
}
response = requests.get(url, headers=headers)
print(response.json())
```

Response:

```json
[
  {
    "id": 63260789,
    "name": "zs-cc-<vpc-id>-<az>",
    "deployType": "CLOUD",
    "platform": "AWS",
    "awsAvailabilityZone": "US_WEST_2A",
    "location": {
      "id": 63260784,
      "name": "<region>-<vpc-id>"
    },
    "ecVMs": [
      {
        "id": 63260794,
        "name": "zs-cc-<ec-group>-VM-<id>",
        "operationalStatus": "INACTIVE",
        "natIp": "<cc-nat-ip>",
        "ziaGateway": "<zia-gateway-ip>"
      }
    ]
  }
]
```

### Cloud & Branch Connector — Forwarding Rules (EC Rules)

These are the endpoints used by the ZTGW ingress design to manage forwarding policies:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/ztw/api/v1/ecRules/ecRdr` | List all forwarding rules |
| `POST` | `/ztw/api/v1/ecRules/ecRdr` | Create a new forwarding rule |
| `PUT` | `/ztw/api/v1/ecRules/ecRdr/:ruleId` | Update an existing rule by ID |

Key fields for ZTGW forwarding rules:

| Field | Purpose |
|-------|---------|
| `name` | Rule name |
| `type` | `"FIREWALL"` |
| `state` | `"ENABLED"` or `"DISABLED"` |
| `forwardMethod` | Forwarding method |
| `destAddresses` | **Destination IPs (EIPs)** — the web server public IPs |
| `ecGroups` | Cloud Connector group to route through |
| `order` | Rule priority |

### ZDX — Start Deep Trace

```python
url = "https://api.zsapi.net/zdx/v1/devices/{device_id}/deeptraces"
payload = {
  "session_name": "{sessionName}",
  "session_length_minutes": 5,
  "probe_device": True
}
headers = {
  "Authorization": "Bearer <Access Token>"
}
response = requests.post(url, headers=headers, json=payload)
```

### ZPA — List Application Segments

> Requires `customerId` (ZPA tenant ID). Obtain from ZIdentity Admin Portal → Integration → API Resources → ZPA OneAPI.

```python
url = "https://api.zsapi.net/zpa/mgmtconfig/v1/admin/customers/{customerId}/application"
params = {"page": 1, "pagesize": 100}
headers = {
  "Authorization": "Bearer <Access Token>"
}
response = requests.get(url, headers=headers, params=params)
```

### Client Connector — Get OTP

```python
url = "https://api.zsapi.net/zcc/papi/public/v1/getOtp"
params = {"udid": "{udid}"}
headers = {
  "Authorization": "Bearer <Access Token>"
}
response = requests.get(url, headers=headers, params=params)
```

---

## 5. Best Practices

- **Adjust token lifetime** — balance convenience and security in ZIdentity
- **Always GET before PUT** — fetch the current resource state before updating to avoid overwriting changes
- **Use UTF-8 encoding** — for all API calls (e.g., `encodeURIComponent()` in JavaScript)
- **Activation required** — for ZIA and Cloud & Branch Connector APIs, changes must be explicitly activated:
  - ZIA: `POST /status/activate`
  - Cloud Connector: `POST /ecAdminActivateStatus/activate`
- **Avoid race conditions** — don't edit via the admin portal UI while scripts are running
- **Batch URL lookups** — max 100 URLs per request, each URL max 1024 characters
- **Handle 409 errors** — add a wait cycle of a few seconds and retry on `EDIT_LOCK_NOT_AVAILABLE`
- **Handle 403 during maintenance** — API returns read-only mode during upgrades; only GET requests work

---

## 6. Error Handling

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request / authentication failure |
| `403` | Read-only mode (maintenance/upgrade) |
| `409` | Edit lock not available (concurrent admin edits) |

Maintenance mode response:

```json
{
  "code": "STATE_READONLY",
  "message": "The API service is undergoing a scheduled upgrade and is in read-only mode."
}
```
