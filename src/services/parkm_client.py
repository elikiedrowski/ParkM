"""
ParkM App API Client
Handles authentication and API calls to the ParkM parking management platform.
Used for refund automation (customer lookup, permit cancellation, payment history).

Sandbox: https://app-api-dev-parkm.azurewebsites.net
Production: https://api.parkm.app
"""
import httpx
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _friendly_cancel_error(raw_text: Optional[str]) -> Optional[str]:
    """Translate the known ParkM/Stripe delayed-cancellation error into a
    clean, neutral CSR message. Returns None if no known pattern matches.

    ParkM surfaces raw Stripe errors as opaque 500s. On delayed cancels we see
    "A canceled subscription can only update its cancellation_details and
    metadata." Investigation (June 2026) found this is *state-dependent* — not
    all paid recurring permits, and NOT (as previously assumed) a subscription
    that was already canceled beforehand: the failing permits were billing
    normally right up to the attempt, and the failed call itself appears to
    cancel the subscription (MOL000621: our call's timestamp matched Stripe's
    "Ended" time to the second). It also reproduces in native .APP, so it's a
    ParkM-side issue, not a wizard bug. Root cause is still under confirmation
    with ParkM (Stephen), so keep this message neutral on cause and remedy.
    """
    if not raw_text:
        return None
    t = str(raw_text).lower()
    if "canceled subscription can only update" in t or "cancellation_details" in t:
        return (
            "ParkM returned a Stripe billing-subscription error, so this "
            "delayed cancellation didn't complete. Please verify the permit's "
            "status in ParkM and flag it to support if it needs follow-up."
        )
    return None


class ParkMClient:
    """Client for ParkM REST API (Azure-hosted, Bearer token auth)."""

    _access_token: Optional[str] = None
    _token_expires_at: float = 0

    def __init__(self):
        self.base_url = os.getenv(
            "PARKM_API_URL",
            "https://app-api-dev-parkm.azurewebsites.net",
        )
        self._username = os.getenv("PARKM_API_USERNAME", "")
        self._password = os.getenv("PARKM_API_PASSWORD", "")
        self._tenant_id = os.getenv("PARKM_API_TENANT_ID", "0")

    # ── Authentication ────────────────────────────────────────────────

    async def _authenticate(self) -> str:
        """Authenticate and cache the bearer token."""
        cls = ParkMClient
        if cls._access_token and time.time() < cls._token_expires_at:
            return cls._access_token

        url = f"{self.base_url}/api/TokenAuth/Authenticate"
        payload = {
            "userNameOrEmailAddress": self._username,
            "password": self._password,
        }
        headers = {
            "Content-Type": "application/json",
            "X-TenantId": self._tenant_id,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result") or {}
        token = result.get("accessToken")
        if not token:
            raise RuntimeError(f"ParkM auth failed: {data.get('error', data)}")

        cls._access_token = token
        # ParkM tokens typically last ~24h; refresh every 20h
        cls._token_expires_at = time.time() + 72000
        logger.info("ParkM API token refreshed")
        return token

    def _invalidate_token(self):
        ParkMClient._access_token = None
        ParkMClient._token_expires_at = 0

    async def _headers(self) -> Dict[str, str]:
        token = await self._authenticate()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-TenantId": self._tenant_id,
        }

    # ── Generic request helpers ───────────────────────────────────────

    async def _get(self, path: str, params: Optional[Dict] = None, timeout: float = 20) -> Any:
        """GET with auto-retry on 401."""
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=headers, params=params)
            if resp.status_code == 401:
                self._invalidate_token()
                headers = await self._headers()
                resp = await client.get(f"{self.base_url}{path}", headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def _post(self, path: str, body: Optional[Dict] = None, params: Optional[Dict] = None, timeout: float = 20) -> Any:
        """POST with auto-retry on 401."""
        headers = await self._headers()
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{self.base_url}{path}", headers=headers, json=body, params=params)
            if resp.status_code == 401:
                self._invalidate_token()
                headers = await self._headers()
                resp = await client.post(f"{self.base_url}{path}", headers=headers, json=body, params=params)
            resp.raise_for_status()
            return resp.json()

    # ── Customer Lookup ───────────────────────────────────────────────

    async def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up a ParkM customer by email address.

        Tries GetCustomerFromEmail first, then validates the returned email
        matches. If it doesn't (sandbox bug returns a default customer),
        falls back to Customers/Search for an exact match.

        Returns customer dict with id, name, orgUnit, accountId, etc.
        Returns None if not found.
        """
        try:
            data = await self._post(
                "/api/services/app/PermitPortal/GetCustomerFromEmail",
                body={"primaryEmailAddress": email},
            )
            result = data.get("result")
            if result and result.get("id"):
                # Verify the returned customer actually matches the requested email
                returned_email = (result.get("primaryEmailAddress") or "").lower()
                if returned_email == email.lower():
                    logger.info(f"Found ParkM customer for {email}: {result['id']}")
                    return result
                # Email mismatch — fall back to search
                logger.warning(
                    f"GetCustomerFromEmail returned mismatched email "
                    f"(requested={email}, got={returned_email}), falling back to search"
                )
                return await self._search_customer_by_email(email)
            return await self._search_customer_by_email(email)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                logger.info(f"GetCustomerFromEmail 500 for {email}, trying search fallback")
                return await self._search_customer_by_email(email)
            raise

    async def _search_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Fallback: search for a customer by email via Customers/Search."""
        try:
            data = await self._post(
                "/api/services/app/Customers/Search",
                body={"filter": email},
                timeout=30,
            )
            items = data.get("result", {}).get("items", [])
            for item in items:
                customer = item.get("customer", item)
                if (customer.get("primaryEmailAddress") or "").lower() == email.lower():
                    logger.info(f"Found ParkM customer via search for {email}: {customer['id']}")
                    return customer
            logger.info(f"No ParkM customer found for {email}")
            return None
        except Exception as e:
            logger.error(f"Customer search fallback failed for {email}: {e}")
            return None

    async def search_vehicles_by_plate(self, plate: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search vehicles by license plate via Vehicles/SearchAzure.

        Each result has plate, customerName, community, but customerId is null —
        callers must follow up with search_customers(name) to get the customer id.
        """
        try:
            data = await self._post(
                "/api/services/app/Vehicles/SearchAzure",
                body={"filter": plate, "maxResultCount": max_results},
                timeout=30,
            )
            return data.get("result", {}).get("items", [])
        except Exception as e:
            logger.error(f"Vehicle plate search failed for '{plate}': {e}")
            return []

    async def search_units(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search units by unit number via Units/Search.

        Returns units with embedded customers array (full customer objects).
        """
        try:
            data = await self._post(
                "/api/services/app/Units/Search",
                body={"filter": query, "maxResultCount": max_results},
                timeout=30,
            )
            return data.get("result", {}).get("items", [])
        except Exception as e:
            logger.error(f"Unit search failed for '{query}': {e}")
            return []

    async def search_customers(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for ParkM customers by any term (name, email, etc.).

        Uses the Customers/Search endpoint which matches against customer-level
        fields (name, email). Does NOT search vehicle plates or unit numbers.

        Returns a list of customer dicts (may be empty).
        """
        try:
            data = await self._post(
                "/api/services/app/Customers/Search",
                body={"filter": query, "maxResultCount": max_results},
                timeout=60,
            )
            items = data.get("result", {}).get("items", [])
            return [item.get("customer", item) for item in items]
        except Exception as e:
            logger.error(f"Customer search failed for '{query}': {e}")
            return []

    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Look up a ParkM customer by their UUID."""
        try:
            data = await self._post(
                "/api/services/app/PermitPortal/GetCustomerFromId",
                body={"id": customer_id},
            )
            return data.get("result")
        except httpx.HTTPStatusError:
            return None

    # ── Permits ───────────────────────────────────────────────────────

    async def get_customer_permits(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get active permits for a customer via GetActiveCustomerVehicles.

        Per Stephen: GetAll requires body params (not query params) and may not
        return portal-purchased permits. GetActiveCustomerVehicles returns
        vehicles with their active permits embedded.
        """
        vehicles = await self.get_customer_vehicles(customer_id)
        return vehicles

    async def get_all_permits(self, customer_id: str) -> Any:
        """Get ALL permits (active + cancelled + expired) for a customer.

        Uses Permits/GetAll with CustomerIdFilter per Stephen's guidance.
        """
        data = await self._get(
            "/api/services/app/Permits/GetAll",
            params={"CustomerIdFilter": customer_id},
        )
        result = data.get("result")
        if isinstance(result, dict):
            return result.get("items", [])
        if isinstance(result, list):
            return result
        return data

    async def get_payments_for_permit(self, permit_id: str) -> List[Dict[str, Any]]:
        """Get the Stripe payment-intent history for a single permit.

        `PermitPortal/GetAllTransactions` is unreliable in production (returns
        an empty list for many real customers even when their permits have
        clearly been charged). `Permits/GetAllPaymentsForPermit` is the
        authoritative per-permit charge feed: it returns all Stripe payment
        intents tied to the permit, including those for cancelled permits.

        Returns a list of dicts shaped like:
            {"id": "pi_...", "created": "ISO-8601", "description": "...", "amount": float}
        """
        try:
            data = await self._get(
                "/api/services/app/Permits/GetAllPaymentsForPermit",
                params={"PermitId": permit_id},
            )
        except httpx.HTTPStatusError:
            return []
        result = data.get("result")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            return result.get("items", [])
        return []

    async def get_permit_details(self, permit_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed permit info for editing/viewing."""
        try:
            data = await self._get(
                "/api/services/app/PermitPortal/GetPermitForView",
                params={"id": permit_id},
            )
            return data.get("result")
        except httpx.HTTPStatusError:
            return None

    async def cancel_permit(self, permit_id: str, send_notice: bool = True) -> bool:
        """Cancel a permit by ID.

        Uses the admin Permits/CancelPermit endpoint.
        Args:
            permit_id: UUID of the permit
            send_notice: Whether to send cancellation email to customer
        Returns:
            True if cancellation succeeded
        """
        try:
            await self._post(
                "/api/services/app/Permits/CancelPermit",
                params={"Id": permit_id, "sendNotice": str(send_notice).lower()},
            )
            logger.info(f"Permit {permit_id} cancelled (notice={send_notice})")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel permit {permit_id}: {e}")
            return False

    async def delay_cancel_permit(
        self,
        permit_id: str,
        cancel_date: str,
        send_notice: bool = True,
        update_next_recurring_date: bool = False,
        next_recurring_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Schedule a delayed cancellation for a permit.

        Instead of cancelling immediately, flags the permit for cancellation
        (isCancelled=true) with a future delayCancellationDate. ParkM's
        background job cancels the permit when that date arrives. The resident
        receives a cancellation notice so they can correct mistakes.

        Approach (confirmed with ParkM/Stephen Lambert + a live test permit
        2026-06-04): setting delayCancellationDate ALONE persists the date (it
        displays on Permit Details) but never enqueues the cancellation — the
        permit lingers Active past its date. ParkM's job only acts on permits
        with isCancelled=true. With isCancelled=true AND a *future*
        delayCancellationDate, the permit stays Active/usable until that date,
        then cancels on schedule (validated: it fired exactly on time and the
        permit's expirationDate is moved to the delay date). permitCancellation
        Reason is NOT required.
        1. GET Permits/GetPermitForEdit — fetch current permit data
        2. Set isCancelled=true + delayCancellationDate on the DTO
        3. (Optionally) set nextRecurringDate to a new value or null to clear
        4. POST Permits/CreateOrEdit — save it back

        The nextRecurringDate update mirrors what .APP's "Actions > Edit >
        Delete Next Recurring Date" does — same endpoint, same DTO field. CSRs
        use this when scheduling a cancellation to prevent an auto-charge from
        firing before the cancellation takes effect.

        Args:
            permit_id: UUID of the permit
            cancel_date: ISO-8601 datetime string for when to cancel
            send_notice: Whether to send cancellation notice email
            update_next_recurring_date: If True, also write nextRecurringDate
                using the next_recurring_date param. If False (default), leave
                the field untouched.
            next_recurring_date: New value for nextRecurringDate (ISO-8601), or
                None to clear it. Only applied when update_next_recurring_date
                is True.
        Returns:
            Dict with `success` (bool) and `error` (str|None). On failure, the
            error string captures whatever ParkM gave us (HTTP status + body, or
            ABP error.message/details) so the caller can surface a useful
            message to the CSR instead of a generic "try manually" fallback.
        """
        try:
            # Step 1: Get current permit data
            edit_data = await self._get(
                "/api/services/app/Permits/GetPermitForEdit",
                params={"Id": permit_id},
            )
            permit_dto = edit_data.get("result", {}).get("permit", edit_data.get("result", {}))
            if not permit_dto or not permit_dto.get("id"):
                msg = f"Could not fetch permit {permit_id} for delay cancel (no DTO returned)"
                logger.error(msg)
                return {"success": False, "error": msg}

            # Step 2: Flag the permit for cancellation and set the date.
            # isCancelled=true is REQUIRED — without it ParkM's background job
            # never picks up the permit and the cancellation silently never
            # fires (the date alone only updates a display column). A future
            # delayCancellationDate makes this a *scheduled* cancel: the permit
            # stays Active until the date, then cancels.
            permit_dto["isCancelled"] = True
            permit_dto["delayCancellationDate"] = cancel_date
            permit_dto["dontSendNotifications"] = not send_notice

            # Step 3: Optionally adjust the next recurring date so the permit
            # doesn't auto-charge before the scheduled cancellation fires.
            if update_next_recurring_date:
                permit_dto["nextRecurringDate"] = next_recurring_date
                logger.info(
                    f"Permit {permit_id} nextRecurringDate set to {next_recurring_date!r}"
                )

            # Step 4: Save back
            result = await self._post(
                "/api/services/app/Permits/CreateOrEdit",
                body=permit_dto,
            )
            success = result.get("success", False)
            if success:
                logger.info(f"Permit {permit_id} delay-cancel scheduled for {cancel_date} (notice={send_notice})")
                return {"success": True, "error": None}

            # ABP error structure is {success: false, error: {message, details}}.
            # Surface message + details explicitly so logs aren't truncated and
            # the widget can show something useful.
            err_obj = result.get("error") or {}
            err_msg = err_obj.get("message") if isinstance(err_obj, dict) else str(err_obj)
            err_details = err_obj.get("details") if isinstance(err_obj, dict) else None
            logger.error(
                f"Permit {permit_id} delay-cancel returned success=false: "
                f"message={err_msg!r} details={err_details!r} full={result!r}"
            )
            friendly = _friendly_cancel_error(f"{err_msg} {err_details}")
            return {
                "success": False,
                "error": friendly or err_msg or err_details or "ParkM CreateOrEdit returned success=false",
            }
        except httpx.HTTPStatusError as e:
            # The most useful failure case: ParkM returned a non-2xx with a
            # body explaining what's wrong. Capture both for the logs and the
            # caller. Without this we used to lose the body entirely.
            body = ""
            try:
                body = e.response.text
            except Exception:
                pass
            status = e.response.status_code if e.response is not None else "?"
            logger.error(
                f"Failed to delay-cancel permit {permit_id}: HTTP {status} body={body[:1000]!r}"
            )
            friendly = _friendly_cancel_error(body)
            return {
                "success": False,
                "error": friendly or (f"ParkM HTTP {status}: {body[:300]}" if body else f"ParkM HTTP {status}"),
            }
        except Exception as e:
            logger.error(f"Failed to delay-cancel permit {permit_id}: {e}", exc_info=True)
            return {"success": False, "error": str(e) or "Unknown error"}

    # ── Vehicles ──────────────────────────────────────────────────────

    async def get_customer_vehicles(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get active vehicles for a customer."""
        data = await self._get(
            "/api/services/app/PermitPortal/GetActiveCustomerVehicles",
            params={"customerId": customer_id},
        )
        return data.get("result", [])

    # ── Payments & Transactions ───────────────────────────────────────

    async def get_customer_transactions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get financial transactions for a customer."""
        data = await self._get(
            "/api/services/app/PermitPortal/GetAllTransactions",
            params={"customerId": customer_id},
        )
        return data.get("result", [])

    async def get_customer_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get Stripe subscriptions for a customer."""
        data = await self._get(
            "/api/services/app/StripePayment/GetCustomerSubscriptions",
            params={"customerId": customer_id},
        )
        return data.get("result", [])

    async def get_customer_balance(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get outstanding balance on customer permits."""
        data = await self._get(
            "/api/services/app/PermitPortal/GetCustomerPermitsBalanceDue",
            params={"customerId": customer_id},
        )
        return data.get("result", [])

    # ── Health ────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Verify API connectivity by fetching session info."""
        data = await self._get("/api/services/app/Session/GetCurrentLoginInformations")
        result = data.get("result", {})
        user = result.get("user", {})
        return {
            "connected": True,
            "user": user.get("userName"),
            "api_version": result.get("application", {}).get("version"),
        }
