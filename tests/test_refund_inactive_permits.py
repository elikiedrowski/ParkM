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
async def test_active_permit_enrichment_sets_last_charge_date_for_eligibility():
    """
    Reproduces Sadie's CP2000004 case: an active/scheduled recurring permit
    with an old effectiveDate but a recent per-permit Stripe charge. The
    customer-wide transaction feed can be empty, so eligibility must use the
    date from GetAllPaymentsForPermit.
    """
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[
        _make_payment(days_ago=27, amount=10.0),
        _make_payment(days_ago=58, amount=10.0),
    ])
    effective = datetime.now(timezone.utc) - timedelta(days=209)
    permit = {
        "id": "cp2000004",
        "permit_type_name": "Carport Permit",
        "permit_name": "CP2000004",
        "effective_date": effective.isoformat().replace("+00:00", "Z"),
        "recurring_price": 10.0,
        "permit_price": 10.0,
        "is_cancelled": False,
    }

    await svc._enrich_permits_with_payment_totals([permit])
    eligibility = svc.evaluate_refund_eligibility(permit, transactions=[])

    assert permit["total_paid_within_window"] == 10.0
    last_charge = datetime.fromisoformat(permit["last_charge_date"])
    assert (datetime.now(timezone.utc) - last_charge).days < 30
    assert eligibility["eligible"] is True
    assert eligibility["refund_amount"] == 10.0
    assert eligibility["days_since_charge"] < 30
    svc.parkm.get_payments_for_permit.assert_awaited_once_with("cp2000004")


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
async def test_recent_effective_date_permit_included():
    """A Daily Guest issued 4 days ago passes via effectiveDate. The per-permit
    Stripe lookup now always runs (needed to distinguish free vs paid permits
    via amount totals), but the permit must still surface in the result."""
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


@pytest.mark.asyncio
async def test_stale_customer_transaction_date_still_triggers_payment_lookup():
    """
    Hardening: PermitPortal/GetAllTransactions can be partially stale rather
    than only empty. If it has an OLD transaction for a permit, the per-permit
    Stripe feed should still be consulted in case there's a newer charge.
    Without this, a permit with a 6-month-old txn-feed entry but a recent
    Stripe charge would be excluded.
    """
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000130", status="Cancelled", effective_days_ago=370)

    # Customer-wide feed has a stale entry — older than the refund window.
    stale_txn_date = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat().replace("+00:00", "Z")
    transactions = [{"permitId": "r000130", "transactionDate": stale_txn_date}]

    # But the per-permit Stripe feed has a recent charge.
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[_make_payment(days_ago=4)])

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=transactions,
        all_permits_raw=[cancelled],
    )

    assert len(result) == 1
    last_charge = datetime.fromisoformat(result[0]["last_charge_date"])
    assert (datetime.now(timezone.utc) - last_charge).days < 30
    svc.parkm.get_payments_for_permit.assert_awaited_once_with("r000130")


@pytest.mark.asyncio
async def test_failed_payment_intents_do_not_count_as_recent_activity():
    """
    Hardening: Stripe creates payment-intent records for every checkout
    attempt, including ones that never completed (status=failed, canceled,
    requires_action, etc.). Treating their `created` timestamp as evidence
    of a charge would inflate the inactive list with permits whose customer
    abandoned a payment but never actually paid.
    """
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000130", status="Cancelled", effective_days_ago=370)

    # All recent payment intents are failed/cancelled — none of them moved money.
    failed_payments = [
        {**_make_payment(days_ago=2), "status": "failed"},
        {**_make_payment(days_ago=4), "status": "canceled"},
        {**_make_payment(days_ago=6), "status": "requires_payment_method"},
    ]
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=failed_payments)

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=[],
        all_permits_raw=[cancelled],
    )

    assert result == []  # No real charge → permit excluded


@pytest.mark.asyncio
async def test_succeeded_payment_among_failed_intents_is_counted():
    """A real successful charge mixed in with failed attempts should still
    surface the permit — the failed ones just get filtered out."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000130", status="Cancelled", effective_days_ago=370)

    payments = [
        {**_make_payment(days_ago=1), "status": "failed"},   # newest, but didn't go through
        {**_make_payment(days_ago=5), "status": "succeeded"},  # actual charge
        {**_make_payment(days_ago=8), "status": "canceled"},
    ]
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=payments)

    result = await svc._get_inactive_permits(
        customer_id="cust-1",
        active_permit_ids=set(),
        transactions=[],
        all_permits_raw=[cancelled],
    )

    assert len(result) == 1
    last_charge = datetime.fromisoformat(result[0]["last_charge_date"])
    # last_charge_date should be the succeeded one (5 days ago), NOT the
    # failed-but-newer one (1 day ago).
    age_days = (datetime.now(timezone.utc) - last_charge).days
    assert 4 <= age_days <= 6


@pytest.mark.asyncio
async def test_refund_amount_uses_charged_total_including_surcharge():
    """Sadie 2026-05-28, ticket #98779: the refund amount must be the actual
    total billed to the card (permit price + credit-card surcharge), not the
    permit's configured base price. A $10 permit charged with a $0.44 CC
    surcharge bills $10.44 — that's the refund amount."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    # Stripe feed reports the full charged total ($10.44), not the $10 base.
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[
        _make_payment(days_ago=3, amount=10.44),
    ])
    permit = {
        "id": "r000017",
        "permit_type_name": "Resident Open Lot Permit",
        "permit_name": "R000017",
        "recurring_price": 10.0,
        "permit_price": 10.0,
        "total_amount": 10.0,
        "is_cancelled": False,
    }

    await svc._enrich_permits_with_payment_totals([permit])
    eligibility = svc.evaluate_refund_eligibility(permit, transactions=[])

    assert permit["last_charge_amount"] == 10.44
    assert eligibility["eligible"] is True
    # NOT 10.0 — the surcharge must be included.
    assert eligibility["refund_amount"] == 10.44


@pytest.mark.asyncio
async def test_refund_amount_falls_back_to_base_price_without_charge_data():
    """When the per-permit Stripe feed has no charge amount (e.g. lookup
    failed), the refund amount falls back to the permit's configured price
    rather than reporting nothing."""
    svc = RefundService.__new__(RefundService)
    permit = {
        "id": "r000018",
        "permit_type_name": "Resident Open Lot Permit",
        "permit_name": "R000018",
        "recurring_price": 25.0,
        "permit_price": 25.0,
        "last_charge_amount": 0.0,  # no usable charge total
        "last_charge_date": (datetime.now(timezone.utc) - timedelta(days=2))
            .isoformat().replace("+00:00", "Z"),
        "total_paid_within_window": 25.0,
        "is_cancelled": False,
    }

    eligibility = svc.evaluate_refund_eligibility(permit, transactions=[])
    assert eligibility["eligible"] is True
    assert eligibility["refund_amount"] == 25.0


def test_park_guard_first_month_is_not_refundable():
    svc = RefundService.__new__(RefundService)
    permit = {
        "id": "pg-1",
        "permit_type_name": "Park Guard",
        "permit_name": "PG000001",
        "recurring_price": 12.0,
        "last_charge_amount": 12.0,
        "last_charge_date": (datetime.now(timezone.utc) - timedelta(days=5))
            .isoformat().replace("+00:00", "Z"),
        "effective_date": (datetime.now(timezone.utc) - timedelta(days=5))
            .isoformat().replace("+00:00", "Z"),
        "total_paid_within_window": 12.0,
        "is_cancelled": False,
    }

    eligibility = svc.evaluate_refund_eligibility(permit, transactions=[])

    assert eligibility["eligible"] is False
    assert "Park Guard" in eligibility["reason"]
    assert eligibility["refund_amount"] is None


def test_park_guard_after_first_month_can_be_refunded():
    svc = RefundService.__new__(RefundService)
    permit = {
        "id": "pg-2",
        "permit_type_name": "Park Guard",
        "permit_name": "PG000002",
        "recurring_price": 12.0,
        "last_charge_amount": 12.0,
        "last_charge_date": (datetime.now(timezone.utc) - timedelta(days=5))
            .isoformat().replace("+00:00", "Z"),
        "effective_date": (datetime.now(timezone.utc) - timedelta(days=45))
            .isoformat().replace("+00:00", "Z"),
        "total_paid_within_window": 12.0,
        "is_cancelled": False,
    }

    eligibility = svc.evaluate_refund_eligibility(permit, transactions=[])

    assert eligibility["eligible"] is True
    assert eligibility["refund_amount"] == 12.0


# ── Reactivation-date vs. last-charge (ticket #102525, permit R000018) ──────


@pytest.mark.asyncio
async def test_reactivation_date_is_not_treated_as_last_charge():
    """Ticket #102525 (R000018): a reactivated permit has effectiveDate ==
    reactivationDate (1 day ago) but its real last charge was 7 days ago. The
    reactivation moved no money, so last_charge_date must be the real charge,
    not the newer reactivation date."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000018", status="Cancelled", effective_days_ago=1)
    # ParkM stamps effectiveDate and reactivationDate together (~ms apart).
    react = datetime.now(timezone.utc) - timedelta(days=1)
    cancelled["permit"]["reactivationDate"] = (
        (react + timedelta(milliseconds=2)).isoformat().replace("+00:00", "Z")
    )
    svc.parkm.get_payments_for_permit = AsyncMock(
        return_value=[_make_payment(days_ago=7, amount=10.44)]
    )

    result = await svc._get_inactive_permits(
        customer_id="cust-1", active_permit_ids=set(), transactions=[],
        all_permits_raw=[cancelled],
    )

    assert len(result) == 1
    last_charge = datetime.fromisoformat(result[0]["last_charge_date"])
    assert (datetime.now(timezone.utc) - last_charge).days == 7
    assert result[0]["last_charge_amount"] == 10.44


@pytest.mark.asyncio
async def test_reactivated_permit_without_payment_is_not_surfaced():
    """A reactivated permit with no real charge must not look recently charged
    just because its effectiveDate was bumped to the reactivation date."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    cancelled = _make_permit(permit_id="r000018b", status="Cancelled", effective_days_ago=1)
    cancelled["permit"]["reactivationDate"] = cancelled["permit"]["effectiveDate"]
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[])

    result = await svc._get_inactive_permits(
        customer_id="cust-1", active_permit_ids=set(), transactions=[],
        all_permits_raw=[cancelled],
    )

    assert result == []


@pytest.mark.asyncio
async def test_recent_effective_date_without_reactivation_still_seeds():
    """Preserve the effectiveDate fallback for recent no-payment permits that
    were NOT reactivated. The reactivation guard must not strip a genuine
    recent effectiveDate (e.g. a freshly issued short-lived permit)."""
    svc = RefundService.__new__(RefundService)
    svc.parkm = AsyncMock()
    recent = _make_permit(
        permit_id="vt-noreact", status="Expired", effective_days_ago=3,
        name="Daily Guest Permit",
    )
    # No reactivationDate on the DTO.
    svc.parkm.get_payments_for_permit = AsyncMock(return_value=[])

    result = await svc._get_inactive_permits(
        customer_id="cust-1", active_permit_ids=set(), transactions=[],
        all_permits_raw=[recent],
    )

    assert len(result) == 1
    assert result[0]["id"] == "vt-noreact"


def test_evaluate_ignores_reactivation_date_as_charge():
    """Active path: with no payment-feed charge, evaluate must not use a
    reactivation-stamped effective_date as the last charge."""
    svc = RefundService.__new__(RefundService)
    react = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    permit = {
        "id": "r-active",
        "permit_type_name": "Resident Open Lot Permit",
        "permit_name": "R000099",
        "effective_date": react,
        "reactivation_date": react,
        "recurring_price": 10.0,
    }

    result = svc.evaluate_refund_eligibility(permit, transactions=[])

    assert result["last_charge_date"] is None
    assert result["eligible"] is False
    assert result["reason"] == "Cannot determine last charge date"
