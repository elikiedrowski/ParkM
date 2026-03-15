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
                "permits": [ permit summaries ],
                "vehicles": [ vehicle summaries ],
            }
        """
        customer = await self.parkm.get_customer_by_email(email)
        if not customer:
            return {"found": False, "customer": None, "permits": [], "vehicles": []}

        customer_id = customer["id"]
        name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip()

        # Fetch permits (required) and vehicles/transactions (best-effort)
        raw_permits = await self.parkm.get_customer_permits(customer_id)
        try:
            vehicles = await self.parkm.get_customer_vehicles(customer_id)
        except Exception:
            logger.warning(f"Could not fetch vehicles for {customer_id}")
            vehicles = []
        try:
            transactions = await self.parkm.get_customer_transactions(customer_id)
        except Exception:
            logger.warning(f"Could not fetch transactions for {customer_id}")
            transactions = []

        permits = []
        for item in raw_permits:
            p = item.get("permit", {})
            permit_summary = {
                "id": p.get("id"),
                "type_name": item.get("permitTypeName", "Unknown"),
                "effective_date": p.get("effectiveDate"),
                "expiration_date": p.get("expirationDate"),
                "is_cancelled": p.get("isCancelled", False),
                "is_recurring": item.get("isRecurring", False),
                "recurring_price": p.get("recurringPrice"),
                "permit_price": p.get("permitPrice") or item.get("permitPrice"),
                "total_amount": item.get("totalAmount"),
                "stripe_id": item.get("stripeId"),
                "subscription_id": item.get("subscriptionId"),
                "vehicle": {
                    "plate": item.get("licensePlate"),
                    "make": item.get("vehicleMakeName"),
                    "model": item.get("vehicleModelName"),
                    "color": item.get("vehicleColorName"),
                    "year": item.get("vehicleYear"),
                },
                "community": item.get("communityName"),
                "balance_due": item.get("balanceDue", 0),
            }
            permits.append(permit_summary)

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
            "vehicles": vehicles,
            "transactions": transactions,
        }

    # ── Step 2: Evaluate Refund Eligibility ───────────────────────────

    def evaluate_refund_eligibility(
        self,
        permit: Dict[str, Any],
        move_out_date: Optional[str] = None,
        transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Check if a permit qualifies for a refund per ParkM policy.

        Rules (from process flow):
        - Customer must have moved out before the last charge
        - Last charge must be within 30 days

        Args:
            permit: Permit summary from lookup_customer()
            move_out_date: ISO date string of when the customer moved out
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

        # Check move-out date if provided
        moved_before_charge = True
        if move_out_date:
            try:
                move_dt = datetime.fromisoformat(move_out_date.replace("Z", "+00:00"))
                if move_dt.tzinfo is None:
                    move_dt = move_dt.replace(tzinfo=timezone.utc)
                moved_before_charge = move_dt <= last_charge
            except (ValueError, TypeError):
                moved_before_charge = False  # Can't verify move-out — deny refund

        # Determine refund amount (use explicit None checks to handle 0 correctly)
        refund_amount = permit.get("recurring_price")
        if refund_amount is None:
            refund_amount = permit.get("permit_price")
        if refund_amount is None:
            refund_amount = permit.get("total_amount")

        eligible = within_window and moved_before_charge

        if not within_window:
            reason = f"Last charge was {days_since} days ago (exceeds {REFUND_WINDOW_DAYS}-day window)"
        elif not moved_before_charge:
            reason = "Customer had not moved out before the last charge date"
        else:
            reason = "Eligible — within 30-day window and moved out before last charge"

        return {
            "eligible": eligible,
            "reason": reason,
            "refund_amount": refund_amount,
            "last_charge_date": last_charge_str,
            "days_since_charge": days_since,
        }

    # ── Step 3: Cancel Permit ─────────────────────────────────────────

    async def cancel_permit(self, permit_id: str, send_notice: bool = True) -> Dict[str, Any]:
        """Cancel a permit in ParkM.

        Returns:
            {"success": bool, "permit_id": str, "message": str}
        """
        success = await self.parkm.cancel_permit(permit_id, send_notice=send_notice)
        return {
            "success": success,
            "permit_id": permit_id,
            "message": "Permit cancelled successfully" if success else "Failed to cancel permit",
        }

    # ── Step 4: Build Accounting Email ────────────────────────────────

    def build_accounting_email(
        self,
        customer_name: str,
        customer_email: str,
        refund_amount: float,
        reason: str,
        permit_type: str = "",
        ticket_id: str = "",
    ) -> Dict[str, Any]:
        """Build the email content to forward to accounting@parkm.com.

        Per the process flow:
        - Reply All on the Zoho ticket
        - Remove the customer's email
        - Add accounting@parkm.com
        - Include: resident email, refund amount, reason

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
        safe_permit = html.escape(permit_type)
        safe_reason = html.escape(reason)

        subject = f"Refund Request - {customer_name}"
        if ticket_id:
            subject += f" (Ticket #{ticket_id})"

        body_html = f"""<p>Hi Accounting,</p>

<p>Please process the following refund:</p>

<ul>
  <li><strong>Resident Email:</strong> {safe_email}</li>
  <li><strong>Resident Name:</strong> {safe_name}</li>
  <li><strong>Refund Amount:</strong> {safe_amount}</li>
  <li><strong>Permit Type:</strong> {safe_permit}</li>
  <li><strong>Reason:</strong> {safe_reason}</li>
</ul>

<p>Please process via ParkM app: Transactions and Payments → Actions → Reverse Charge</p>

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
        move_out_date: Optional[str] = None,
        reason: str = "Customer requested cancellation/refund",
        ticket_id: str = "",
        auto_cancel: bool = False,
    ) -> Dict[str, Any]:
        """Run the full refund evaluation workflow.

        This does NOT auto-cancel or auto-refund by default — it evaluates
        and returns recommendations for the CSR to confirm.

        Args:
            customer_email: Customer's email address
            permit_id: Specific permit to evaluate (optional; if None, returns all)
            move_out_date: When customer moved out (ISO date, optional)
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

            eligibility = self.evaluate_refund_eligibility(permit, move_out_date, transactions)

            # Step 3: Auto-cancel if requested AND eligible for refund
            cancel_result = None
            if auto_cancel and eligibility["eligible"] and not permit.get("is_cancelled"):
                cancel_result = await self.cancel_permit(permit["id"])

            # Step 4: Build accounting email if eligible
            accounting_email = None
            if eligibility["eligible"]:
                accounting_email = self.build_accounting_email(
                    customer_name=customer["name"],
                    customer_email=customer["email"],
                    refund_amount=eligibility["refund_amount"],
                    reason=reason,
                    permit_type=permit.get("type_name", ""),
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
