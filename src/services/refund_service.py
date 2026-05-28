"""
Refund & Cancellation Automation Service
Implements the refund/cancellation workflow from the ParkM process flow:

1. Look up customer in ParkM by email
2. Review permits and find the relevant one
3. Check last transaction date for 30-day refund window
4. Cancel the permit
5. If refund eligible, forward details to accounting@parkm.com
6. Update Zoho ticket status

This service is called from the widget or API endpoints to automate
the manual steps CSRs currently perform.
"""
import asyncio
import html
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.services.parkm_client import ParkMClient

logger = logging.getLogger(__name__)

REFUND_WINDOW_DAYS = 30
ACCOUNTING_EMAIL = os.environ.get("ACCOUNTING_EMAIL", "accounting@parkm.com")


class RefundService:
    """Orchestrates the refund/cancellation workflow."""

    def __init__(self):
        self.parkm = ParkMClient()

    # ── Step 1: Customer Lookup ───────────────────────────────────────

    async def lookup_customer(self, email: str) -> Dict[str, Any]:
        """Find customer in ParkM by email and return their account summary."""
        customer = await self.parkm.get_customer_by_email(email)
        if not customer:
            return {"found": False, "customer": None, "permits": [], "inactive_permits": [], "vehicles": []}
        return await self._build_customer_summary(customer, fallback_email=email)

    async def lookup_customer_by_id(self, customer_id: str) -> Dict[str, Any]:
        """Find customer in ParkM by ID and return their account summary."""
        customer = await self.parkm.get_customer_by_id(customer_id)
        if not customer:
            return {"found": False, "customer": None, "permits": [], "inactive_permits": [], "vehicles": []}
        return await self._build_customer_summary(customer)

    async def _build_customer_summary(
        self, customer: Dict[str, Any], fallback_email: str = ""
    ) -> Dict[str, Any]:
        """Shared logic to assemble customer + permits + inactive permits."""
        customer_id = customer["id"]
        name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip()

        # Fetch permits via GetActiveCustomerVehicles (per Stephen's guidance)
        # This returns vehicles with embedded active permits
        raw_vehicles = await self.parkm.get_customer_permits(customer_id)
        try:
            transactions = await self.parkm.get_customer_transactions(customer_id)
        except Exception:
            logger.warning(f"Could not fetch transactions for {customer_id}")
            transactions = []

        permits = []
        vehicles = []
        active_permit_ids = set()
        for item in raw_vehicles:
            v = item.get("vehicle", {})
            p = item.get("activePermit", {})
            if not p or not p.get("id"):
                continue

            vehicles.append(item)
            active_permit_ids.add(p.get("id"))
            permit_summary = self._build_permit_summary(p, item, v)
            permits.append(permit_summary)

        # Fetch all permits once — used by two helpers below.
        try:
            all_permits_raw = await self.parkm.get_all_permits(customer_id)
        except Exception:
            logger.warning(f"Could not fetch all permits for {customer_id}")
            all_permits_raw = []

        # Once a permit has delayCancellationDate set, ParkM stops returning it
        # as the vehicle's activePermit, but Permits/GetAll still reports it as
        # status=Active. Merge those scheduled-to-cancel permits into the
        # active list so they don't disappear from the wizard.
        scheduled_to_cancel = await self._get_scheduled_to_cancel_permits(
            customer_id, active_permit_ids, all_permits_raw
        )
        for sp in scheduled_to_cancel:
            active_permit_ids.add(sp["id"])
            permits.append(sp)

        # Fetch inactive permits (cancelled/expired) for the 30-day window.
        inactive_permits = await self._get_inactive_permits(
            customer_id, active_permit_ids, transactions, all_permits_raw
        )

        # Enrich active + scheduled-to-cancel permits with the same Stripe
        # payment totals that inactive permits already carry. Without this,
        # the free-permit eligibility guard in evaluate_refund_eligibility
        # only fires for inactive permits — and "free monthly recurring"
        # permits scheduled for cancellation (e.g. R000016, ticket #95512)
        # were still showing ELIGIBLE FOR REFUND.
        await self._enrich_permits_with_payment_totals(permits)

        return {
            "found": True,
            "customer": {
                "id": customer_id,
                "name": name,
                "email": customer.get("primaryEmailAddress") or fallback_email,
                "phone": customer.get("mobilePhone"),
                "account_id": customer.get("accountId"),
                "org_unit_id": customer.get("organizationUnitId"),
                "created": customer.get("creationTime"),
            },
            "permits": permits,
            "inactive_permits": inactive_permits,
            "vehicles": vehicles,
            "transactions": transactions,
        }

    def _build_permit_summary(
        self, p: Dict[str, Any], item: Dict[str, Any], v: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a normalized permit summary dict from raw API data."""
        if v is None:
            v = item.get("vehicle", {})
        return {
            "id": p.get("id"),
            # type_name kept for backward-compat (it's the property name here).
            # Prefer permit_type_name / community in the widget.
            "type_name": item.get("community") or p.get("communityName") or "Unknown",
            "permit_type_name": item.get("permitTypeName"),
            "permit_number": p.get("name"),
            "space_number": item.get("lotSpace"),
            "time_zone": item.get("timeZone"),
            "effective_date": p.get("effectiveDate"),
            "expiration_date": p.get("expirationDate"),
            "is_cancelled": p.get("isCancelled", False),
            "is_recurring": item.get("isRecurring", p.get("isRecurring", False)),
            "recurring_price": p.get("recurringPrice"),
            "next_recurring_date": p.get("nextRecurringDate"),
            "permit_price": p.get("amountDue") or p.get("price"),
            "total_amount": p.get("amountDue") or p.get("price"),
            "stripe_id": None,
            "subscription_id": None,
            "vehicle": {
                "plate": v.get("licensePlate"),
                "make": item.get("vehicleMakeName") or v.get("makeName"),
                "model": item.get("vehicleModelName") or v.get("modelName"),
                "color": item.get("vehicleColorName") or v.get("colorName"),
                "year": v.get("year"),
            },
            "community": item.get("community") or p.get("communityName"),
            "balance_due": p.get("amountDue", 0),
            "permit_name": p.get("name"),
            "delay_cancellation_date": p.get("delayCancellationDate"),
        }

    async def _get_scheduled_to_cancel_permits(
        self,
        customer_id: str,
        active_permit_ids: set,
        all_permits_raw: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find permits that are scheduled-to-cancel (delayCancellationDate set)
        but no longer returned by GetActiveCustomerVehicles.

        ParkM removes a permit from the vehicle's activePermit slot the moment
        delayCancellationDate is set, even though the permit is still status=
        Active until the cancellation date arrives. Without this helper those
        permits disappear from the wizard entirely. We scan Permits/GetAll
        for status=Active permits not in active_permit_ids, then call
        GetPermitForEdit on each to read delayCancellationDate (Permits/GetAll
        summaries omit that field — same gotcha as in scripts/reactivate_all
        _permits.py). Permits with the delay date set get a normal active-
        shape summary so the existing widget banner renders.
        """
        if not all_permits_raw:
            return []

        results: List[Dict[str, Any]] = []
        for raw in all_permits_raw:
            permit_data = raw.get("permit") or raw
            permit_id = permit_data.get("id")
            if not permit_id or permit_id in active_permit_ids:
                continue
            status = permit_data.get("status", "")
            if status != "Active":
                continue

            # GetAll omits delayCancellationDate — fetch the edit DTO to confirm.
            try:
                edit_data = await self.parkm._get(
                    "/api/services/app/Permits/GetPermitForEdit",
                    params={"Id": permit_id},
                )
            except Exception:
                logger.warning(
                    f"Could not fetch edit DTO for permit {permit_id} (scheduled-cancel scan)"
                )
                continue
            permit_dto = (edit_data.get("result") or {}).get("permit") or edit_data.get("result") or {}
            delay_date = permit_dto.get("delayCancellationDate")
            if not delay_date:
                # Active in GetAll but not actually scheduled to cancel — skip.
                continue

            results.append({
                "id": permit_id,
                # type_name kept on its legacy meaning for backward compat with
                # the old widget. New widget reads permit_type_name / community.
                "type_name": raw.get("permitTypeName") or raw.get("communityName") or "Unknown",
                "permit_type_name": raw.get("permitTypeName"),
                "permit_number": permit_dto.get("name") or permit_data.get("name"),
                "space_number": raw.get("spaceNumber"),
                "time_zone": raw.get("timeZone"),
                "effective_date": permit_dto.get("effectiveDate") or permit_data.get("effectiveDate"),
                "expiration_date": permit_dto.get("expirationDate") or permit_data.get("expirationDate"),
                "is_cancelled": False,
                "status": status,
                "is_recurring": raw.get("isRecurring") or permit_dto.get("isRecurring", False),
                "recurring_price": permit_dto.get("recurringPrice"),
                "next_recurring_date": permit_dto.get("nextRecurringDate"),
                "permit_price": permit_dto.get("price") or permit_dto.get("amountDue"),
                "total_amount": permit_dto.get("amountDue"),
                "vehicle": {
                    "plate": raw.get("licensePlate"),
                    "make": raw.get("vehicleMakeName"),
                    "model": raw.get("vehicleModelName"),
                    "color": raw.get("vehicleColorName"),
                    "year": raw.get("vehicleYear"),
                },
                "community": raw.get("communityName"),
                "balance_due": raw.get("balanceDue", 0),
                "permit_name": permit_dto.get("name") or permit_data.get("name"),
                "delay_cancellation_date": delay_date,
            })
        return results

    async def _enrich_permits_with_payment_totals(
        self, permits: List[Dict[str, Any]]
    ) -> None:
        """For each permit (modified in place), fetch its Stripe payment
        history and attach `total_paid_within_window`. This is what lets the
        free-permit eligibility guard fire for active and scheduled-to-cancel
        permits, not just inactive ones — a "free monthly recurring" permit
        looks identical to a paid one without this enrichment.
        """
        if not permits:
            return
        cutoff = datetime.now(timezone.utc) - timedelta(days=REFUND_WINDOW_DAYS)
        ids = [p.get("id") for p in permits if p.get("id")]
        if not ids:
            return
        results = await asyncio.gather(
            *(self.parkm.get_payments_for_permit(pid) for pid in ids),
            return_exceptions=True,
        )
        payments_by_id: Dict[str, List[Dict[str, Any]]] = {}
        for pid, result in zip(ids, results):
            if isinstance(result, Exception):
                logger.warning(f"get_payments_for_permit failed for {pid}: {result}")
                payments_by_id[pid] = []
            else:
                payments_by_id[pid] = result or []
        for permit in permits:
            pid = permit.get("id")
            if not pid:
                continue
            latest, total_paid, latest_amount = self._payment_window_summary(
                payments_by_id.get(pid, []),
                window_start=cutoff,
            )
            permit["total_paid_within_window"] = total_paid
            # Actual total charged on the most recent charge (incl. credit-card
            # surcharge / convenience fee). Used as the refund amount so the
            # wizard stops under-reporting it as the permit's base price.
            permit["last_charge_amount"] = latest_amount
            # Active permits don't otherwise carry last_charge_date. Without
            # this, evaluate_refund_eligibility falls back to effective_date
            # (the original sign-up date for recurring permits) even when the
            # per-permit payment feed shows a recent charge.
            if latest is not None:
                permit["last_charge_date"] = latest.isoformat()

    async def _get_inactive_permits(
        self,
        customer_id: str,
        active_permit_ids: set,
        transactions: List[Dict[str, Any]],
        all_permits_raw: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find inactive permits with activity within the last 30 days.

        Source of truth for "what was charged in the last 30 days":
        1. The customer-wide transactions list (PermitPortal/GetAllTransactions),
           if it's populated. This is unreliable in prod — it returns [] for
           many real customers — so we treat it as best-effort.
        2. Permits/GetAllPaymentsForPermit per inactive permit. This is the
           authoritative Stripe charge feed and works for cancelled permits.
        3. effectiveDate as a last resort (only useful for short-lived permits
           like Daily Guest where signup ≈ activity).
        """
        if not all_permits_raw:
            return []

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=REFUND_WINDOW_DAYS)

        # Best-effort: build a map of permit_id -> most recent transaction date
        # from the customer-wide list. Often empty in prod.
        txn_dates: Dict[str, datetime] = {}
        for txn in transactions:
            permit_id = txn.get("permitId") or txn.get("permit_id")
            txn_date_str = txn.get("creationTime") or txn.get("transactionDate") or txn.get("date")
            if not permit_id or not txn_date_str:
                continue
            try:
                txn_dt = datetime.fromisoformat(txn_date_str.replace("Z", "+00:00"))
                if permit_id not in txn_dates or txn_dt > txn_dates[permit_id]:
                    txn_dates[permit_id] = txn_dt
            except (ValueError, TypeError):
                continue

        # First pass: collect non-active permits and seed ref_date from any
        # cheap signal (customer-wide transactions list, or effectiveDate if
        # in-window). We always follow up with the per-permit Stripe feed —
        # it's the only way to know whether the customer was ever actually
        # charged (free permits look identical to paid permits otherwise).
        candidates: List[Tuple[Dict[str, Any], Optional[datetime]]] = []
        for raw in all_permits_raw:
            permit_data = raw.get("permit", raw)
            permit_id = permit_data.get("id")
            if not permit_id or permit_id in active_permit_ids:
                continue
            status = permit_data.get("status", "")
            if status == "Active":
                continue

            ref_date = txn_dates.get(permit_id)
            eff_dt: Optional[datetime] = None
            eff_str = permit_data.get("effectiveDate")
            if eff_str:
                try:
                    eff_dt = datetime.fromisoformat(eff_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    eff_dt = None

            if ref_date is None and eff_dt is not None and eff_dt >= cutoff:
                ref_date = eff_dt

            candidates.append((raw, ref_date))

        # Second pass: fetch payment history concurrently for every candidate.
        # We need the amount totals, not just the date, to distinguish
        # free permits from real charges.
        lookup_ids = [(raw.get("permit", raw)).get("id") for raw, _ in candidates]
        payments_by_permit: Dict[str, List[Dict[str, Any]]] = {}
        if lookup_ids:
            results = await asyncio.gather(
                *(self.parkm.get_payments_for_permit(pid) for pid in lookup_ids),
                return_exceptions=True,
            )
            for pid, result in zip(lookup_ids, results):
                if isinstance(result, Exception):
                    logger.warning(f"get_payments_for_permit failed for {pid}: {result}")
                    payments_by_permit[pid] = []
                else:
                    payments_by_permit[pid] = result or []

        inactive_permits: List[Dict[str, Any]] = []
        for raw, ref_date in candidates:
            permit_data = raw.get("permit", raw)
            permit_id = permit_data.get("id")
            status = permit_data.get("status", "")

            latest, total_paid_in_window, latest_amount = self._payment_window_summary(
                payments_by_permit.get(permit_id, []),
                window_start=cutoff,
            )
            # Per-permit Stripe feed wins if it shows a more recent charge —
            # the customer-wide transactions list can be stale.
            if latest is not None and (ref_date is None or latest > ref_date):
                ref_date = latest

            if ref_date is None or ref_date < cutoff:
                continue

            summary = {
                "id": permit_id,
                # type_name kept on its legacy meaning (permitTypeName-or-community)
                # for backward compat with the old widget. New widget uses the
                # explicit permit_type_name / community fields below.
                "type_name": raw.get("permitTypeName") or raw.get("communityName") or "Unknown",
                "permit_type_name": raw.get("permitTypeName"),
                "permit_number": permit_data.get("name"),
                "space_number": raw.get("spaceNumber"),
                "time_zone": raw.get("timeZone"),
                "effective_date": permit_data.get("effectiveDate"),
                "expiration_date": permit_data.get("expirationDate"),
                "is_cancelled": status == "Cancelled",
                "status": status,
                "is_recurring": raw.get("isRecurring", False),
                "recurring_price": permit_data.get("recurringPrice"),
                "next_recurring_date": permit_data.get("nextRecurringDate"),
                "permit_price": permit_data.get("permitPrice") or raw.get("permitPrice"),
                "total_amount": raw.get("totalAmount"),
                "vehicle": {
                    "plate": raw.get("licensePlate"),
                    "make": raw.get("vehicleMakeName"),
                    "model": raw.get("vehicleModelName"),
                    "color": raw.get("vehicleColorName"),
                    "year": raw.get("vehicleYear"),
                },
                "community": raw.get("communityName"),
                "balance_due": raw.get("balanceDue", 0),
                "permit_name": permit_data.get("name"),
                "last_charge_date": ref_date.isoformat(),
                "total_paid_within_window": total_paid_in_window,
                # Full amount billed on the most recent charge (incl. CC
                # surcharge / convenience fee) — used as the refund amount.
                "last_charge_amount": latest_amount,
            }
            inactive_permits.append(summary)

        return inactive_permits

    # Stripe payment-intent / ParkM payment statuses that mean money did NOT
    # move. We don't count these as evidence the permit was recently charged.
    # Anything else (succeeded, paid, captured, or no status field at all) is
    # included — be liberal about unknown statuses so we don't accidentally
    # hide a real charge because ParkM tweaked the field shape.
    _NON_CHARGE_STATUSES = frozenset({
        "failed", "canceled", "cancelled", "void", "voided",
        "requires_payment_method", "requires_action", "requires_confirmation",
        "requires_capture", "incomplete", "incomplete_expired",
    })

    @classmethod
    def _payment_window_summary(
        cls,
        payments: List[Dict[str, Any]],
        window_start: Optional[datetime] = None,
    ) -> Tuple[Optional[datetime], float, float]:
        """Inspect a Permits/GetAllPaymentsForPermit list and return
        (latest_successful_date, total_paid_within_window, latest_charge_amount).

        Skips payment intents whose status indicates the charge never
        completed (failed, canceled, requires_*) — Stripe creates intent
        records for every abandoned checkout, and counting those as charges
        would let free/abandoned permits look eligible for refund.

        If `window_start` is provided, `total_paid_within_window` only sums
        successful payments dated at-or-after that cutoff. Otherwise sums all
        successful payments in the list.

        `latest_charge_amount` is the amount of the most recent successful
        charge — i.e. the full total billed to the card, which already
        includes the credit-card surcharge / convenience fee (ParkM bills the
        permit price + that fee as a single Stripe charge). This is what the
        refund amount should be, not the permit's configured base price.
        Returns 0.0 if there were no successful charges.
        """
        latest: Optional[datetime] = None
        latest_amount: float = 0.0
        total: float = 0.0
        for pay in payments:
            status = str(pay.get("status") or pay.get("state") or "").strip().lower()
            if status in cls._NON_CHARGE_STATUSES:
                continue
            d = pay.get("created") or pay.get("creationTime") or pay.get("date")
            if not d:
                continue
            try:
                dt = datetime.fromisoformat(d.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue
            try:
                amount = float(pay.get("amount") or 0)
            except (TypeError, ValueError):
                amount = 0.0
            if latest is None or dt > latest:
                latest = dt
                latest_amount = amount
            if window_start is None or dt >= window_start:
                if amount > 0:
                    total += amount
        return latest, total, latest_amount

    # ── Step 2: Evaluate Refund Eligibility ───────────────────────────

    def evaluate_refund_eligibility(
        self,
        permit: Dict[str, Any],
        transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Check if a permit qualifies for a refund per ParkM policy.

        Rules:
        - Guest permits are never eligible for refund
        - Last charge must be within 30 days

        Args:
            permit: Permit summary from lookup_customer()
            transactions: Customer transaction list from lookup (used for last charge date)

        Returns:
            {
                "eligible": bool,
                "reason": str,
                "refund_amount": float or None,
                "last_charge_date": str or None,
                "days_since_charge": int or None,
            }
        """
        # Guest permits are never eligible for refund.
        # Check across permit_type_name (e.g. "Guest Permit"), permit_name (the
        # display code like GP000123), and the legacy type_name fallback.
        guest_check = " ".join([
            permit.get("permit_type_name") or "",
            permit.get("permit_name") or "",
            permit.get("type_name") or "",
        ]).lower()
        if "guest" in guest_check:
            return {
                "eligible": False,
                "reason": "Guest permits are not eligible for refund",
                "refund_amount": None,
                "last_charge_date": None,
                "days_since_charge": None,
            }

        # Park Guard can be refunded after the first month, but ParkM policy
        # does not refund the first payment / first month.
        park_guard_check = " ".join([
            permit.get("permit_type_name") or "",
            permit.get("permit_name") or "",
            permit.get("type_name") or "",
            permit.get("community") or "",
        ]).lower()
        if "park guard" in park_guard_check:
            effective_str = permit.get("effective_date")
            try:
                effective_date = (
                    datetime.fromisoformat(effective_str.replace("Z", "+00:00"))
                    if effective_str
                    else None
                )
            except (ValueError, TypeError):
                effective_date = None
            if effective_date is not None:
                first_month_days = (datetime.now(timezone.utc) - effective_date).days
                if first_month_days <= REFUND_WINDOW_DAYS:
                    return {
                        "eligible": False,
                        "reason": "Park Guard first payment / first month is not eligible for refund",
                        "refund_amount": None,
                        "last_charge_date": permit.get("last_charge_date"),
                        "days_since_charge": first_month_days,
                    }

        # No-money-moved guard — if the Stripe per-permit feed shows no
        # successful charge with amount > 0 in the 30-day window, there's
        # nothing to refund. Applies to inactive permits (caught ticket
        # #95512 in the inactive list) AND active / scheduled-to-cancel
        # permits with chargeFrequency=Free (caught the same #95512 R000016
        # on Sadie's second pass — free monthly recurring still showed
        # ELIGIBLE because we weren't enriching active permits with the
        # payment totals).
        if "total_paid_within_window" in permit:
            try:
                paid = float(permit.get("total_paid_within_window") or 0)
            except (TypeError, ValueError):
                paid = 0.0
            if paid <= 0:
                # Differentiate "truly free permit, no price configured"
                # from "paid permit but no recent charge" — same outcome
                # (no refund), clearer message for the CSR.
                priced = any(
                    permit.get(k) not in (None, 0, 0.0)
                    for k in ("recurring_price", "permit_price", "total_amount")
                )
                reason = (
                    "No charge within the 30-day refund window — nothing to refund"
                    if priced
                    else "Free permit — customer was not charged"
                )
                return {
                    "eligible": False,
                    "reason": reason,
                    "refund_amount": None,
                    "last_charge_date": permit.get("last_charge_date"),
                    "days_since_charge": None,
                }

        # Find the most recent transaction date for this permit.
        # Inactive permits already carry last_charge_date (from _get_inactive_permits);
        # for active permits we look it up from the transaction list.
        # Fall back to effective_date if no transactions available.
        last_charge_str = permit.get("last_charge_date")
        if not last_charge_str and transactions:
            permit_txns = []
            for txn in transactions:
                txn_permit_id = txn.get("permitId") or txn.get("permit_id")
                txn_date = txn.get("creationTime") or txn.get("transactionDate") or txn.get("date")
                if txn_date and (not txn_permit_id or txn_permit_id == permit.get("id")):
                    permit_txns.append(txn_date)
            if permit_txns:
                permit_txns.sort(reverse=True)
                last_charge_str = permit_txns[0]

        if not last_charge_str:
            last_charge_str = permit.get("effective_date")

        if not last_charge_str:
            return {
                "eligible": False,
                "reason": "Cannot determine last charge date",
                "refund_amount": None,
                "last_charge_date": None,
                "days_since_charge": None,
            }

        try:
            last_charge = datetime.fromisoformat(last_charge_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return {
                "eligible": False,
                "reason": f"Invalid charge date format: {last_charge_str}",
                "refund_amount": None,
                "last_charge_date": last_charge_str,
                "days_since_charge": None,
            }

        now = datetime.now(timezone.utc)
        days_since = (now - last_charge).days

        # Check 30-day window
        within_window = days_since <= REFUND_WINDOW_DAYS

        # Determine refund amount.
        #
        # Prefer the ACTUAL total billed on the most recent charge
        # (last_charge_amount, from the Stripe per-permit feed). That figure
        # already includes the credit-card surcharge / convenience fee — both
        # are billed as part of the same charge — and excludes ACH bounce fees
        # (those are separate balance charges, not permit payments, and per
        # ParkM policy are never refunded). Sadie flagged 2026-05-28 that the
        # wizard was reporting only the permit's base price ($10) and dropping
        # the surcharge ($0.44), so accounting received a short refund amount.
        #
        # Fall back to the permit's configured price when there's no charge
        # data (use explicit None checks to handle a configured price of 0).
        refund_amount = None
        charged = permit.get("last_charge_amount")
        if charged is not None:
            try:
                charged = float(charged)
            except (TypeError, ValueError):
                charged = 0.0
            if charged > 0:
                refund_amount = charged
        if refund_amount is None:
            refund_amount = permit.get("recurring_price")
        if refund_amount is None:
            refund_amount = permit.get("permit_price")
        if refund_amount is None:
            refund_amount = permit.get("total_amount")

        eligible = within_window

        if not within_window:
            reason = f"Last charge was {days_since} days ago (exceeds {REFUND_WINDOW_DAYS}-day window)"
        else:
            reason = "Eligible — within 30-day refund window"

        return {
            "eligible": eligible,
            "reason": reason,
            "refund_amount": refund_amount,
            "last_charge_date": last_charge_str,
            "days_since_charge": days_since,
        }

    # ── Step 3: Cancel Permit ─────────────────────────────────────────

    async def cancel_permit(
        self,
        permit_id: str,
        send_notice: bool = True,
        cancel_date: Optional[str] = None,
        update_next_recurring_date: bool = False,
        next_recurring_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Cancel a permit in ParkM (immediate or delayed).

        Args:
            permit_id: UUID of the permit
            send_notice: Whether to send cancellation notice to customer
            cancel_date: If provided (ISO-8601), schedule a delayed cancellation
                         instead of cancelling immediately.
            update_next_recurring_date: If True (and cancel_date is set), also
                update the permit's nextRecurringDate via the same edit call.
            next_recurring_date: New value for nextRecurringDate (ISO-8601) or
                None to clear it. Only used when update_next_recurring_date.

        Returns:
            {"success": bool, "permit_id": str, "message": str, "cancel_type": str}
        """
        if cancel_date:
            delay_result = await self.parkm.delay_cancel_permit(
                permit_id,
                cancel_date=cancel_date,
                send_notice=send_notice,
                update_next_recurring_date=update_next_recurring_date,
                next_recurring_date=next_recurring_date,
            )
            success = bool(delay_result.get("success"))
            err = delay_result.get("error")
            return {
                "success": success,
                "permit_id": permit_id,
                "cancel_type": "delayed",
                "cancel_date": cancel_date,
                "error": err,
                "message": (
                    f"Permit cancellation scheduled for {cancel_date}"
                    if success
                    else (err or "Failed to schedule permit cancellation")
                ),
            }
        else:
            success = await self.parkm.cancel_permit(permit_id, send_notice=send_notice)
            return {
                "success": success,
                "permit_id": permit_id,
                "cancel_type": "immediate",
                "message": "Permit cancelled successfully" if success else "Failed to cancel permit",
            }

    # ── Step 4: Build Accounting Email ────────────────────────────────

    def build_accounting_email(
        self,
        customer_name: str,
        customer_email: str,
        refund_amount: float,
        property_name: str = "",
        ticket_id: str = "",
        refund_reason: str = "",
    ) -> Dict[str, Any]:
        """Build the email content to forward to accounting@parkm.com.

        Per the process flow:
        - Reply All on the Zoho ticket
        - Remove the customer's email
        - Add accounting@parkm.com
        - Include: resident name, resident email, property name, refund amount

        Returns:
            {
                "to": ACCOUNTING_EMAIL,
                "subject": str,
                "body_html": str,
            }
        """
        amount_str = f"${refund_amount:.2f}" if refund_amount else "See ticket"

        # HTML-escape all user-provided values to prevent XSS
        safe_name = html.escape(customer_name)
        safe_email = html.escape(customer_email)
        safe_amount = html.escape(amount_str)
        safe_property = html.escape(property_name)
        safe_reason = html.escape(refund_reason) if refund_reason else ""

        subject = f"Refund Request - {customer_name}"
        if ticket_id:
            subject += f" (Ticket #{ticket_id})"

        reason_li = f"\n  <li><strong>Reason for Refund:</strong> {safe_reason}</li>" if safe_reason else ""

        body_html = f"""<p>Hi Accounting,</p>

<p>Please process the following refund:</p>

<ul>
  <li><strong>Resident Name:</strong> {safe_name}</li>
  <li><strong>Resident Email:</strong> {safe_email}</li>
  <li><strong>Property Name:</strong> {safe_property}</li>
  <li><strong>Refund Amount:</strong> {safe_amount}</li>{reason_li}
</ul>

<p>Thank you,<br>
ParkM Support Team</p>"""

        return {
            "to": ACCOUNTING_EMAIL,
            "subject": subject,
            "body_html": body_html,
        }

    # ── Full Workflow ─────────────────────────────────────────────────

    async def process_refund_request(
        self,
        customer_email: str,
        permit_id: Optional[str] = None,
        reason: str = "Customer requested cancellation/refund",
        ticket_id: str = "",
        auto_cancel: bool = False,
        cancel_date: Optional[str] = None,
        send_notice: bool = True,
        update_next_recurring_date: bool = False,
        next_recurring_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the full refund evaluation workflow.

        This does NOT auto-cancel or auto-refund by default — it evaluates
        and returns recommendations for the CSR to confirm.

        Args:
            customer_email: Customer's email address
            permit_id: Specific permit to evaluate (optional; if None, returns all)
            reason: Reason for the refund request
            ticket_id: Zoho ticket ID for reference
            auto_cancel: If True, cancel the permit automatically

        Returns:
            Full workflow result with customer info, permit details,
            eligibility assessment, and recommended actions.
        """
        # Step 1: Lookup
        lookup = await self.lookup_customer(customer_email)
        if not lookup["found"]:
            return {
                "status": "customer_not_found",
                "message": f"No ParkM account found for {customer_email}",
                "next_action": "Request license plate and bank statement screenshot from customer",
                "lookup": lookup,
            }

        customer = lookup["customer"]
        permits = lookup["permits"]
        inactive_permits = lookup.get("inactive_permits", [])
        # When evaluating a specific permit, look in both active and inactive
        # so the inactive-permit refund flow works. When listing all, default
        # to active only (inactive surface separately in the widget).
        if permit_id:
            candidates = permits + inactive_permits
        else:
            candidates = [p for p in permits if not p.get("is_cancelled")]

        if not candidates:
            return {
                "status": "no_active_permits",
                "message": f"Customer {customer['name']} has no active permits",
                "customer": customer,
                "permits": permits,
            }

        # Step 2: Evaluate eligibility
        transactions = lookup.get("transactions", [])
        results = []
        for permit in candidates:
            if permit_id and permit["id"] != permit_id:
                continue

            eligibility = self.evaluate_refund_eligibility(permit, transactions)

            # Step 3: Auto-cancel if requested AND eligible for refund.
            # If the permit is already fully cancelled, skip the API call but
            # return a synthetic success so the widget renders the right
            # message and continues to the accounting-email step.
            cancel_result = None
            if auto_cancel and eligibility["eligible"]:
                if permit.get("is_cancelled"):
                    cancel_result = {
                        "success": True,
                        "permit_id": permit["id"],
                        "cancel_type": "already_cancelled",
                        "message": "Permit was already cancelled",
                    }
                elif permit.get("delay_cancellation_date"):
                    # Already scheduled to cancel — re-running delay_cancel_permit
                    # would mutate the existing schedule (or fail). Return a
                    # synthetic success so the widget renders the right message
                    # and continues to the accounting-email step.
                    cancel_result = {
                        "success": True,
                        "permit_id": permit["id"],
                        "cancel_type": "already_scheduled",
                        "cancel_date": permit.get("delay_cancellation_date"),
                        "message": "Permit was already scheduled to cancel",
                    }
                else:
                    cancel_result = await self.cancel_permit(
                        permit["id"],
                        send_notice=send_notice,
                        cancel_date=cancel_date,
                        update_next_recurring_date=update_next_recurring_date,
                        next_recurring_date=next_recurring_date,
                    )

            # Step 4: Build accounting email if eligible
            accounting_email = None
            if eligibility["eligible"]:
                accounting_email = self.build_accounting_email(
                    customer_name=customer["name"],
                    customer_email=customer["email"],
                    refund_amount=eligibility["refund_amount"],
                    property_name=permit.get("community") or permit.get("type_name", ""),
                    ticket_id=ticket_id,
                    refund_reason=reason or "",
                )

            results.append({
                "permit": permit,
                "eligibility": eligibility,
                "cancel_result": cancel_result,
                "accounting_email": accounting_email,
            })

        # Determine overall status
        any_eligible = any(r["eligibility"]["eligible"] for r in results)
        status = "refund_eligible" if any_eligible else "refund_not_eligible"

        return {
            "status": status,
            "customer": customer,
            "permits_evaluated": len(results),
            "results": results,
            "transactions": lookup.get("transactions", []),
            "next_action": (
                "Forward refund details to accounting@parkm.com and set ticket to 'Waiting on Accounting'"
                if any_eligible
                else "Inform customer they do not qualify for a refund; send Terms & Conditions"
            ),
        }
