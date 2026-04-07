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
    ) -> bool:
        """Schedule a delayed cancellation for a permit.

        Instead of cancelling immediately, sets the permit's delayCancellationDate
        field. ParkM's background job cancels the permit when that date arrives.
        The resident receives a cancellation notice so they can correct mistakes.

        Approach (discovered via Swagger):
        1. GET Permits/GetPermitForEdit — fetch current permit data
        2. Set delayCancellationDate on the DTO
        3. POST Permits/CreateOrEdit — save it back

        Args:
            permit_id: UUID of the permit
            cancel_date: ISO-8601 datetime string for when to cancel
            send_notice: Whether to send cancellation notice email
        Returns:
            True if the delay cancellation was scheduled successfully
        """
        try:
            # Step 1: Get current permit data
            edit_data = await self._get(
                "/api/services/app/Permits/GetPermitForEdit",
                params={"Id": permit_id},
            )
            permit_dto = edit_data.get("result", {}).get("permit", edit_data.get("result", {}))
            if not permit_dto or not permit_dto.get("id"):
                logger.error(f"Could not fetch permit {permit_id} for delay cancel")
                return False

            # Step 2: Set delay cancellation date and notice preference
            permit_dto["delayCancellationDate"] = cancel_date
            permit_dto["dontSendNotifications"] = not send_notice

            # Step 3: Save back
            result = await self._post(
                "/api/services/app/Permits/CreateOrEdit",
                body=permit_dto,
            )
            success = result.get("success", False)
            if success:
                logger.info(f"Permit {permit_id} delay-cancel scheduled for {cancel_date} (notice={send_notice})")
            else:
                logger.error(f"Permit delay-cancel returned success=false: {result}")
            return success
        except Exception as e:
            logger.error(f"Failed to delay-cancel permit {permit_id}: {e}")
            return False

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
