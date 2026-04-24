#!/usr/bin/env python3
"""
probe-endpoints.py — Read-only discovery of ZIA OneAPI object shapes.

Enumerates the EXACT fields available on common OneAPI resources (Location,
LocationGroup, Sublocation, WorkloadGroup, SourceIPGroup, URLFilterRule,
firewallFilteringRules, ecRules, ecgroup, networkServices, etc.) so you can
design integrations against the right primitives with the right field names.

Strictly READ-ONLY. Never issues a PUT/POST/DELETE. Safe against any tenant.

Usage:
  source .env    # populate ZS_VANITY_DOMAIN, ZS_CLIENT_ID, ZS_CLIENT_SECRET
  ./scripts/probe-endpoints.py [--report-dir reports/probe-<ts>]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def env(name: str, required: bool = True) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v and required:
        sys.exit(f"[zia-probe] missing env var: {name} (source .env first)")
    return v


def _strip_scheme(host: str) -> str:
    if host.startswith("https://"):
        return host[len("https://"):]
    if host.startswith("http://"):
        return host[len("http://"):]
    return host


def get_token(vanity: str, client_id: str, client_secret: str) -> str:
    vanity = _strip_scheme(vanity).rstrip("/")
    body = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()
    req = urllib.request.Request(
        f"https://{vanity}/oauth2/v1/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:600]
        sys.exit(f"[zia-probe] token HTTP {e.code}: {body}")
    tok = d.get("access_token")
    if not tok:
        sys.exit(f"[zia-probe] no access_token in response: {d}")
    return tok


def api_get(base: str, token: str, path: str, params: dict | None = None) -> tuple[int, Any]:
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"_body": body[:800]}


def sample_shape(obj: Any, depth: int = 2) -> Any:
    """Return a simplified shape: field names and their value-types (not values)."""
    if isinstance(obj, dict):
        if depth <= 0:
            return "{...}"
        out = {}
        for k, v in obj.items():
            if isinstance(v, dict):
                out[k] = sample_shape(v, depth - 1)
            elif isinstance(v, list):
                if v and isinstance(v[0], (dict, list)):
                    out[k] = [sample_shape(v[0], depth - 1)]
                else:
                    out[k] = f"[{type(v[0]).__name__ if v else '?'}]"
            else:
                out[k] = type(v).__name__
        return out
    if isinstance(obj, list):
        return [sample_shape(obj[0], depth)] if obj else []
    return type(obj).__name__


def first_sample(obj: Any) -> Any:
    """Return the first dict in a list, or the object if it's already a dict."""
    if isinstance(obj, list) and obj:
        return obj[0] if isinstance(obj[0], dict) else None
    if isinstance(obj, dict):
        return obj
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-dir", default=None)
    args = ap.parse_args()

    vanity = env("ZS_VANITY_DOMAIN")
    client_id = env("ZS_CLIENT_ID")
    client_secret = env("ZS_CLIENT_SECRET")
    api_base = env("ZS_API_BASE_URL", required=False) or "https://api.zsapi.net"

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    report_dir = Path(args.report_dir or f"reports/zia-probe-{ts}")
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"[zia-probe] vanity={vanity} api={api_base} report={report_dir}")
    token = get_token(vanity, client_id, client_secret)
    print(f"[zia-probe] token acquired (len={len(token)})")

    # Endpoints relevant to the on-prem-WDS sync target decision.
    # Each is (label, path, params)
    endpoints: list[tuple[str, str, dict]] = [
        ("locations",               "/zia/api/v1/locations",               {"pageSize": 50}),
        ("locations-lite",          "/zia/api/v1/locations/lite",          {"pageSize": 50}),
        ("location-groups",         "/zia/api/v1/locations/groups",        {"pageSize": 50}),
        ("location-groups-lite",    "/zia/api/v1/locations/groups/lite",   {"pageSize": 50}),
        ("ip-source-groups",        "/zia/api/v1/ipSourceGroups",          {}),
        ("ip-source-groups-lite",   "/zia/api/v1/ipSourceGroups/lite",     {}),
        ("url-filter-rules",        "/zia/api/v1/urlFilteringRules",       {}),
        ("workload-groups-ztw",     "/ztw/api/v1/workloadGroups",          {}),
        ("workload-groups-zia",     "/zia/api/v1/workloadGroups",          {}),
        ("public-cloud-info",       "/ztw/api/v1/publicCloudInfo",         {}),
    ]

    summary: list[dict[str, Any]] = []
    location_ids: list[tuple[int, str]] = []  # (id, name) for sublocation probe

    for label, path, params in endpoints:
        code, data = api_get(api_base, token, path, params)
        (report_dir / f"{label}.json").write_text(json.dumps(data, indent=2))
        count = len(data) if isinstance(data, list) else (1 if isinstance(data, dict) else 0)
        sample = first_sample(data)
        shape = sample_shape(sample, depth=3) if sample else None
        summary.append({
            "label": label,
            "path": path,
            "http": code,
            "ok": 200 <= code < 300,
            "count": count,
            "shape": shape,
        })
        badge = "ok" if 200 <= code < 300 else f"HTTP {code}"
        print(f"  [{badge:>7}]  {label:<24}  count={count}")
        if label == "locations-lite" and isinstance(data, list):
            for item in data[:5]:
                if isinstance(item, dict) and item.get("id"):
                    location_ids.append((item["id"], item.get("name", "")))

    # Per-location sublocation probe (first location only — shape is uniform)
    if location_ids:
        loc_id, loc_name = location_ids[0]
        code, data = api_get(api_base, token, f"/zia/api/v1/locations/{loc_id}/sublocations", {})
        (report_dir / "sublocations-first-location.json").write_text(json.dumps({"location_id": loc_id, "location_name": loc_name, "data": data}, indent=2))
        count = len(data) if isinstance(data, list) else 0
        sample = first_sample(data)
        shape = sample_shape(sample, depth=3) if sample else None
        summary.append({
            "label": "sublocations (first loc)",
            "path": f"/zia/api/v1/locations/{loc_id}/sublocations",
            "http": code,
            "ok": 200 <= code < 300,
            "count": count,
            "shape": shape,
        })
        print(f"  [{'ok' if 200 <= code < 300 else 'HTTP ' + str(code):>7}]  sublocations (loc={loc_name}) count={count}")

    # findings.md
    lines = [
        "# ZIA OneAPI Probe — Shapes for On-Prem WDS Targets",
        "",
        f"- tenant (vanity): `{vanity}`",
        f"- api base: `{api_base}`",
        f"- run: `{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}`",
        "",
        "## Endpoint availability",
        "",
        "| Label | Path | HTTP | Count |",
        "| --- | --- | --- | --- |",
    ]
    for s in summary:
        lines.append(f"| `{s['label']}` | `{s['path']}` | {s['http']} | {s['count']} |")

    lines += [
        "",
        "## Object shapes (first sample per endpoint)",
        "",
    ]
    for s in summary:
        if not s["ok"] or not s["shape"]:
            continue
        lines.append(f"### `{s['label']}`")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(s["shape"], indent=2))
        lines.append("```")
        lines.append("")

    (report_dir / "findings.md").write_text("\n".join(lines))
    print(f"\n[zia-probe] report: {report_dir / 'findings.md'}")

    return 0 if all(s["ok"] for s in summary) else 1


if __name__ == "__main__":
    sys.exit(main())
