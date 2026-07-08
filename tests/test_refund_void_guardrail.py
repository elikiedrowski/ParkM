"""
Tests for the double-refund guardrail: a charge already reversed/refunded
(a VOIDED receipt) must be excluded from refund eligibility so a CSR doesn't
refund it twice. The signal comes from Receipts/GetAllByPermit's `isVoided`
flag — the Stripe payment feed (GetAllPaymentsForPermit) does NOT expose
refunds. Ticket #102525.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.services.refund_service import RefundService


def _recent(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _permit(voided, voided_days_ago=3):
    return {
        "id": "p1",
        "permit_name": "R000020",
        "is_cancelled": False,
        "is_recurring": True,
        "recurring_price": 10.0,
        "permit_price": 10.0,
        "last_charge_date": _recent(2),
        "last_charge_amount": 10.44,
        "last_charge_voided": voided,
        "last_charge_voided_date": _recent(voided_days_ago) if voided else None,
    }


def test_voided_last_charge_is_not_eligible():
    svc = RefundService.__new__(RefundService)
    elig = svc.evaluate_refund_eligibility(_permit(voided=True, voided_days_ago=4), transactions=[])
    assert elig["eligible"] is False
    assert elig["already_refunded"] is True
    assert "Already refunded 4 days ago" in elig["reason"]
    assert "check with accounting" in elig["reason"].lower()
    assert elig["refund_amount"] is None


def test_voided_today_says_today():
    svc = RefundService.__new__(RefundService)
    elig = svc.evaluate_refund_eligibility(_permit(voided=True, voided_days_ago=0), transactions=[])
    assert elig["eligible"] is False
    assert "Already refunded today" in elig["reason"]


def test_non_voided_last_charge_stays_eligible():
    svc = RefundService.__new__(RefundService)
    elig = svc.evaluate_refund_eligibility(_permit(voided=False), transactions=[])
    assert elig["eligible"] is True
    assert elig.get("already_refunded") is None


@pytest.mark.asyncio
async def test_helper_detects_voided_latest_charge():
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    vdate = _recent(1)
    svc.parkm._get = AsyncMock(return_value={"result": {"items": [
        {"receipt": {"total": 10.44, "transactionDate": _recent(2), "isVoided": True, "voidedDate": vdate}},
        {"receipt": {"total": 10.44, "transactionDate": _recent(35), "isVoided": False}},
    ]}})
    voided, vd = await svc._last_charge_refund_status("p1")
    assert voided is True
    assert vd == vdate


@pytest.mark.asyncio
async def test_helper_uses_latest_charge_not_older_voids():
    # Latest charge is NOT voided; an older one is → the refundable charge is
    # the latest, so the permit is NOT already-refunded.
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    svc.parkm._get = AsyncMock(return_value={"result": {"items": [
        {"receipt": {"total": 10.0, "transactionDate": _recent(2), "isVoided": False}},
        {"receipt": {"total": 10.0, "transactionDate": _recent(35), "isVoided": True, "voidedDate": _recent(34)}},
    ]}})
    voided, vd = await svc._last_charge_refund_status("p1")
    assert voided is False


@pytest.mark.asyncio
async def test_helper_fails_open_on_error():
    # A receipts-lookup failure must never wrongly block a legitimate refund.
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    svc.parkm._get = AsyncMock(side_effect=Exception("boom"))
    voided, vd = await svc._last_charge_refund_status("p1")
    assert voided is False
    assert vd is None
