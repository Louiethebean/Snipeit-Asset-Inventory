#!/usr/bin/env python3
"""Audit a Snipe-IT inventory for unassigned, stale, and warranty-expiring assets.

Usage:
    export SNIPEIT_URL=https://snipeit.example.com
    export SNIPEIT_TOKEN=your_api_token
    python snipeit_audit.py --stale-days 90 --warranty-warn-days 30 --format md

Hits the Snipe-IT REST API (GET /api/v1/hardware) directly. No live instance
is required to run the tests -- the API-parsing logic is unit-tested against
fixture JSON shaped like Snipe-IT's actual response.
"""
import argparse
import csv
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import requests


@dataclass
class Asset:
    asset_tag: str
    name: str
    assigned_to: Optional[str]
    last_checkin_date: Optional[date]
    purchase_date: Optional[date]
    warranty_months: int
    status: str

    @property
    def warranty_expiry(self) -> Optional[date]:
        if not self.purchase_date or not self.warranty_months:
            return None
        # approximate months as 30 days to avoid a calendar dependency
        return self.purchase_date + timedelta(days=30 * self.warranty_months)

    def is_unassigned(self) -> bool:
        return self.assigned_to is None

    def days_since_checkin(self, as_of: date) -> Optional[int]:
        if not self.last_checkin_date:
            return None
        return (as_of - self.last_checkin_date).days

    def warranty_days_remaining(self, as_of: date) -> Optional[int]:
        expiry = self.warranty_expiry
        if expiry is None:
            return None
        return (expiry - as_of).days


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_asset(raw: Dict) -> Asset:
    assigned = raw.get("assigned_to")
    assigned_name = None
    if isinstance(assigned, dict):
        assigned_name = assigned.get("name")

    last_checkin = raw.get("last_checkin")
    if isinstance(last_checkin, dict):
        last_checkin = last_checkin.get("date") or last_checkin.get("datetime")

    return Asset(
        asset_tag=raw.get("asset_tag", ""),
        name=raw.get("name", "Unnamed asset"),
        assigned_to=assigned_name,
        last_checkin_date=_parse_date(last_checkin),
        purchase_date=_parse_date(raw.get("purchase_date")),
        warranty_months=int(raw.get("warranty_months") or 0),
        status=(raw.get("status_label") or {}).get("name", "Unknown") if isinstance(raw.get("status_label"), dict) else "Unknown",
    )


def fetch_all_assets(base_url: str, token: str, page_size: int = 50) -> List[Dict]:
    """Page through GET /api/v1/hardware and return raw asset dicts."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    assets: List[Dict] = []
    offset = 0

    while True:
        resp = requests.get(
            f"{base_url}/api/v1/hardware",
            headers=headers,
            params={"limit": page_size, "offset": offset},
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("rows", [])
        assets.extend(rows)

        if len(rows) < page_size:
            break
        offset += page_size

    return assets


def find_unassigned(assets: List[Asset]) -> List[Asset]:
    return [a for a in assets if a.is_unassigned()]


def find_stale(assets: List[Asset], stale_days: int, as_of: date) -> List[Asset]:
    stale = []
    for a in assets:
        days = a.days_since_checkin(as_of)
        if days is not None and days >= stale_days:
            stale.append(a)
    return stale


def find_warranty_expiring(assets: List[Asset], warn_days: int, as_of: date) -> List[Asset]:
    expiring = []
    for a in assets:
        remaining = a.warranty_days_remaining(as_of)
        if remaining is not None and remaining <= warn_days:
            expiring.append(a)
    return expiring


def to_markdown(
    unassigned: List[Asset], stale: List[Asset], warranty_expiring: List[Asset], as_of: date
) -> str:
    lines = [f"# Snipe-IT Asset Audit ({as_of.isoformat()})", ""]
    lines.append(f"**Unassigned assets:** {len(unassigned)}")
    lines.append(f"**Stale assets (no recent check-in):** {len(stale)}")
    lines.append(f"**Warranty expiring or expired:** {len(warranty_expiring)}")
    lines.append("")

    if unassigned:
        lines.append("## Unassigned Assets")
        lines.append("| Tag | Name | Status |")
        lines.append("|---|---|---|")
        for a in unassigned:
            lines.append(f"| {a.asset_tag} | {a.name} | {a.status} |")
        lines.append("")

    if warranty_expiring:
        lines.append("## Warranty Expiring / Expired")
        lines.append("| Tag | Name | Warranty Expiry | Days Remaining |")
        lines.append("|---|---|---|---|")
        for a in warranty_expiring:
            lines.append(
                f"| {a.asset_tag} | {a.name} | {a.warranty_expiry} | {a.warranty_days_remaining(as_of)} |"
            )

    return "\n".join(lines) + "\n"


def to_csv(unassigned: List[Asset], stale: List[Asset], warranty_expiring: List[Asset], out) -> None:
    writer = csv.writer(out)
    writer.writerow(["category", "asset_tag", "name", "status"])
    for a in unassigned:
        writer.writerow(["unassigned", a.asset_tag, a.name, a.status])
    for a in stale:
        writer.writerow(["stale", a.asset_tag, a.name, a.status])
    for a in warranty_expiring:
        writer.writerow(["warranty_expiring", a.asset_tag, a.name, a.status])


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a Snipe-IT inventory for risk indicators.")
    parser.add_argument("--stale-days", type=int, default=90)
    parser.add_argument("--warranty-warn-days", type=int, default=30)
    parser.add_argument("--format", choices=["md", "csv"], default="md")
    args = parser.parse_args()

    base_url = os.environ.get("SNIPEIT_URL")
    token = os.environ.get("SNIPEIT_TOKEN")
    if not base_url or not token:
        sys.stderr.write("Set SNIPEIT_URL and SNIPEIT_TOKEN environment variables.\n")
        return 1

    raw_assets = fetch_all_assets(base_url, token)
    assets = [parse_asset(a) for a in raw_assets]
    today = date.today()

    unassigned = find_unassigned(assets)
    stale = find_stale(assets, args.stale_days, today)
    warranty_expiring = find_warranty_expiring(assets, args.warranty_warn_days, today)

    if args.format == "md":
        sys.stdout.write(to_markdown(unassigned, stale, warranty_expiring, today))
    else:
        to_csv(unassigned, stale, warranty_expiring, sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
