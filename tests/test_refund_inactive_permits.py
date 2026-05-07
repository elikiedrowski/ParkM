"""
Tests for RefundService._get_inactive_permits — specifically the fallback to
Permits/GetAllPaymentsForPermit when the customer-wide transactions feed is
empty (the production scenario for ticket #93450).
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.services.refund_service import RefundService


def _make_permit(*, permit_id, status, effective_days_ago, name="Resident Open Lot Permit, $10",
                 community="Claro High Point", plate="CO-CLZT05"):
    eff = datetime.now(timezone.utc) - timedelta(days=effective_days_ago)
    return {
        "permit": {
            "id": permit_id,
            "name": permit_id,
            "status": status,
            "effectiveDate": eff.isoformat().replace("+00:00", "Z"),
            "recurringPrice": 10.0,
            "permitPrice": None,
        },
        "permitTypeName": name,
        "communityName": community,
        "licensePlate": plate,
        "isRecurring": False,
        "balanceDue": 0,
        "totalAmount": None,
    }


def _make_payment(days_ago, amount=10.0):
    created = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return {
        "id": f"pi_{days_ago}",
        "created": created.isoformat().replace("+00:00", "Z"),
        "amount": amount,
        "description": "Stripe charge",
    }


@pytest.mark.asyncio
async def test_cancelled_permit_with_recent_payment_is_included():
    """
    Reproduces ticket #93450: cancelled recurring permit, signed up a year
    ago, charged 6 days ago. Customer-wide GetAllTransactions returns []
    (the production failure mode). The per-permit Stripe lookup must surface
    the recent charge so the permit shows up in the wizard.
    """
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000130", status="Cancelled", effective_days_ago=370)
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[
        _make_payment(days_ago=6),
        _make_payment(days_ago=36),
        _make_payment(days_ago=66),
    ])

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=[],
        all_permits_raw=[cancelled],
    )

    assert len(result) == 1
    permit = result[0]
    assert permit["id"] == "r000130"
    assert permit["is_cancelled"] is True
    assert permit["recurring_price"] == 10.0
    last_charge = datetime.fromisoformat(permit["last_charge_date"])
    assert (datetime.now(timezone.utc) - last_charge).days < 30
    svc.parkm.get_payments_for_permit.assert_awaited_once_with("r000130")


@pytest.mark.asyncio
async def test_cancelled_permit_with_only_old_payments_is_excluded():
    """The other cancelled permit (R000131) — last paid 6 months ago — must
    stay excluded so we don't surface stale refund candidates."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000131", status="Cancelled", effective_days_ago=370,
                             plate="CO-BXJS03")
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[_make_payment(days_ago=180)])

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=[],
        all_permits_raw=[cancelled],
    )

    assert result == []


@pytest.mark.asyncio
async def test_recent_effective_date_skips_payment_lookup():
    """A Daily Guest issued 4 days ago passes on effectiveDate alone; we
    should not waste an API call on it."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    expired_recent = _make_permit(
        permit_id="vt2000003", status="Expired", effective_days_ago=4,
        name="Daily Guest Permit",
    )
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[])

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=[],
        all_permits_raw=[expired_recent],
    )

    assert len(result) == 1
    assert result[0]["id"] == "vt2000003"
    svc.parkm.get_payments_for_permit.assert_not_awaited()


@pytest.mark.asyncio
async def test_active_permits_are_filtered_out():
    """Permits already surfaced in the active list shouldn't appear here too."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    active = _make_permit(permit_id="active-1", status="Active", effective_days_ago=2)
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[])

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids={"active-1"},
        transactions=[],
        all_permits_raw=[active],
    )

    assert result == []
    svc.parkm.get_payments_for_permit.assert_not_awaited()
