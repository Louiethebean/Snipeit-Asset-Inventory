import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from snipeit_audit import (  # noqa: E402
    fetch_all_assets,
    find_stale,
    find_unassigned,
    find_warranty_expiring,
    parse_asset,
    to_markdown,
)

SAMPLE_ASSETS = [
    {
        "asset_tag": "AST-001",
        "name": "Dell Latitude 5420",
        "assigned_to": {"name": "Jane Doe"},
        "last_checkin": {"date": "2026-06-01"},
        "purchase_date": "2023-01-15",
        "warranty_months": 36,
        "status_label": {"name": "Deployed"},
    },
    {
        "asset_tag": "AST-002",
        "name": "Spare Monitor",
        "assigned_to": None,
        "last_checkin": {"date": "2026-01-01"},
        "purchase_date": "2022-01-01",
        "warranty_months": 24,
        "status_label": {"name": "Ready to Deploy"},
    },
    {
        "asset_tag": "AST-003",
        "name": "Loaner Laptop",
        "assigned_to": None,
        "last_checkin": None,
        "purchase_date": "2026-05-01",
        "warranty_months": 12,
        "status_label": {"name": "Ready to Deploy"},
    },
]


def test_parse_asset_extracts_assigned_user():
    asset = parse_asset(SAMPLE_ASSETS[0])
    assert asset.assigned_to == "Jane Doe"
    assert asset.asset_tag == "AST-001"


def test_parse_asset_handles_unassigned():
    asset = parse_asset(SAMPLE_ASSETS[1])
    assert asset.assigned_to is None
    assert asset.is_unassigned()


def test_parse_asset_computes_warranty_expiry():
    asset = parse_asset(SAMPLE_ASSETS[0])
    # purchased 2023-01-15, 36 months warranty (30-day month approximation) -> 2025-12-30
    assert asset.warranty_expiry == date(2025, 12, 30)


def test_find_unassigned_filters_correctly():
    assets = [parse_asset(a) for a in SAMPLE_ASSETS]
    unassigned = find_unassigned(assets)
    assert len(unassigned) == 2
    assert all(a.assigned_to is None for a in unassigned)


def test_find_stale_uses_days_since_checkin():
    assets = [parse_asset(a) for a in SAMPLE_ASSETS]
    as_of = date(2026, 6, 23)
    stale = find_stale(assets, stale_days=90, as_of=as_of)
    # AST-002 last checked in 2026-01-01, well over 90 days before 2026-06-23
    assert any(a.asset_tag == "AST-002" for a in stale)
    assert not any(a.asset_tag == "AST-001" for a in stale)


def test_find_warranty_expiring_flags_expired():
    assets = [parse_asset(a) for a in SAMPLE_ASSETS]
    as_of = date(2026, 6, 23)
    expiring = find_warranty_expiring(assets, warn_days=30, as_of=as_of)
    # AST-002 purchased 2022-01-01 + 24mo warranty already expired by mid-2026
    assert any(a.asset_tag == "AST-002" for a in expiring)


def test_to_markdown_reports_counts():
    assets = [parse_asset(a) for a in SAMPLE_ASSETS]
    as_of = date(2026, 6, 23)
    unassigned = find_unassigned(assets)
    stale = find_stale(assets, 90, as_of)
    expiring = find_warranty_expiring(assets, 30, as_of)
    md = to_markdown(unassigned, stale, expiring, as_of)
    assert "Unassigned assets:** 2" in md


@patch("snipeit_audit.requests.get")
def test_fetch_all_assets_pages_until_short_page(mock_get):
    page1 = MagicMock()
    page1.json.return_value = {"rows": SAMPLE_ASSETS[:2]}
    page1.raise_for_status.return_value = None

    page2 = MagicMock()
    page2.json.return_value = {"rows": SAMPLE_ASSETS[2:]}
    page2.raise_for_status.return_value = None

    mock_get.side_effect = [page1, page2]

    assets = fetch_all_assets("https://snipeit.example.com", "fake-token", page_size=2)
    assert len(assets) == 3
    assert mock_get.call_count == 2
