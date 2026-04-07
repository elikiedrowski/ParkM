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
import html
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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
        """Find customer in ParkM and return their account summary.

        Returns:
            {
                "found": bool,
                "customer": { id, name, email, ... } or None,
                "permits": [ active permit summaries ],
                "inactive_permits": [ inactive permits charged within 30 days ],
                "vehicles": [ vehicle summaries ],
            }
        """
        customer = await self.parkm.get_customer_by_email(email)
        if not customer:
            return {"found": False, "customer": None, "permits": [], "inactive_permits": [], "vehicles": []}

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

        # Fetch all permits (active + inactive) to find recently-charged inactive ones
        inactive_permits = await self._get_inactive_permits(
            customer_id, active_permit_ids, transactions
        )

        return {
            "found": True,
            "customer": {
                "id": customer_id,
                "name": name,
                "email": customer.get("primaryEmailAddress") or email,
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
            "type_name": item.get("community") or p.get("communityName") or "Unknown",
            "effective_date": p.get("effectiveDate"),
            "expiration_date": p.get("expirationDate"),
            "is_cancelled": p.get("isCancelled", False),
            "is_recurring": item.get("isRecurring", p.get("isRecurring", False)),
            "recurring_price": p.get("recurringPrice"),
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
        }

    async def _get_inactive_permits(
        self,
        customer_id: str,
        active_permit_ids: set,
        transactions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find inactive permits with activity within the last 30 days.

        Uses Permits/GetAll (per Stephen's guidance) to get all permits
        including cancelled/expired, then filters to those not in the active
        set and within the 30-day window based on last charge or effective date.
        """
        try:
            all_permits_raw = await self.parkm.get_all_permits(customer_id)
        except Exception:
            logger.warning(f"Could not fetch all permits for {customer_id}")
            return []

        if not all_permits_raw:
            return []

        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=REFUND_WINDOW_DAYS)

        # Build a map of permit_id -> most recent transaction date
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

        inactive_permits = []
        for raw in all_permits_raw:
            permit_data = raw.get("permit", raw)
            permit_id = permit_data.get("id")
            if not permit_id or permit_id in active_permit_ids:
                continue

            # Check status — use permit.status field ("Cancelled", "Expired", etc.)
            status = permit_data.get("status", "")
            if status == "Active":
                continue

            # Determine the reference date for the 30-day filter:
            # prefer last transaction date, fall back to effective date
            ref_date = txn_dates.get(permit_id)
            if not ref_date:
                eff_str = permit_data.get("effectiveDate")
                if eff_str:
                    try:
                        ref_date = datetime.fromisoformat(eff_str.replace("Z", "+00:00"))
                    except (ValueError, TypeError):
                        continue

            if not ref_date or ref_date < cutoff:
                continue

            # Build summary from the GetAll data structure
            summary = {
                "id": permit_id,
                "type_name": raw.get("permitTypeName") or raw.get("communityName") or "Unknown",
                "effective_date": permit_data.get("effectiveDate"),
                "expiration_date": permit_data.get("expirationDate"),
                "is_cancelled": status == "Cancelled",
                "status": status,
                "is_recurring": raw.get("isRecurring", False),
                "recurring_price": permit_data.get("recurringPrice"),
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
            }
            inactive_permits.append(summary)

        return inactive_permits

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
        # Guest permits are never eligible for refund
        permit_name = (permit.get("permit_name") or permit.get("type_name") or "").lower()
        if "guest" in permit_name:
            return {
                "eligible": False,
                "reason": "Guest permits are not eligible for refund",
                "refund_amount": None,
                "last_charge_date": None,
                "days_since_charge": None,
            }

        if permit.get("is_cancelled"):
            return {
                "eligible": False,
                "reason": "Permit is already cancelled",
                "refund_amount": None,
                "last_charge_date": None,
                "days_since_charge": None,
            }

        # Find the most recent transaction date for this permit.
        # Fall back to effective_date if no transactions available.
        last_charge_str = None
        if transactions:
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

        # Determine refund amount (use explicit None checks to handle 0 correctly)
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
    ) -> Dict[str, Any]:
        """Cancel a permit in ParkM (immediate or delayed).

        Args:
            permit_id: UUID of the permit
            send_notice: Whether to send cancellation notice to customer
            cancel_date: If provided (ISO-8601), schedule a delayed cancellation
                         instead of cancelling immediately.

        Returns:
            {"success": bool, "permit_id": str, "message": str, "cancel_type": str}
        """
        if cancel_date:
            success = await self.parkm.delay_cancel_permit(
                permit_id, cancel_date=cancel_date, send_notice=send_notice
            )
            return {
                "success": success,
                "permit_id": permit_id,
                "cancel_type": "delayed",
                "cancel_date": cancel_date,
                "message": (
                    f"Permit cancellation scheduled for {cancel_date}"
                    if success
                    else "Failed to schedule permit cancellation"
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

        subject = f"Refund Request - {customer_name}"
        if ticket_id:
            subject += f" (Ticket #{ticket_id})"

        body_html = f"""<p>Hi Accounting,</p>

<p>Please process the following refund:</p>

<ul>
  <li><strong>Resident Name:</strong> {safe_name}</li>
  <li><strong>Resident Email:</strong> {safe_email}</li>
  <li><strong>Property Name:</strong> {safe_property}</li>
  <li><strong>Refund Amount:</strong> {safe_amount}</li>
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
        active_permits = [p for p in permits if not p.get("is_cancelled")]

        if not active_permits:
            return {
                "status": "no_active_permits",
                "message": f"Customer {customer['name']} has no active permits",
                "customer": customer,
                "permits": permits,
            }

        # Step 2: Evaluate eligibility
        transactions = lookup.get("transactions", [])
        results = []
        for permit in active_permits:
            if permit_id and permit["id"] != permit_id:
                continue

            eligibility = self.evaluate_refund_eligibility(permit, transactions)

            # Step 3: Auto-cancel if requested AND eligible for refund
            cancel_result = None
            if auto_cancel and eligibility["eligible"] and not permit.get("is_cancelled"):
                cancel_result = await self.cancel_permit(
                    permit["id"], cancel_date=cancel_date
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
