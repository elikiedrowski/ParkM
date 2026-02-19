"""
Zoho Desk API Client
Handles all interactions with Zoho Desk API
"""
import httpx
import logging
from typing import Dict, List, Any, Optional
from src.config import get_settings

logger = logging.getLogger(__name__)


class ZohoDeskClient:
    """Client for Zoho Desk API operations"""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.zoho_base_url
        self.org_id = self.settings.zoho_org_id
        self.data_center = self.settings.zoho_data_center
        self.access_token = None

    def _log_zoho_call(self, call_type: str, ticket_id: str = None, success: bool = True, error: str = None):
        """Log a Zoho API call for analytics tracking."""
        try:
            from src.services.analytics_logger import log_api_usage
            log_api_usage(
                provider="zoho",
                call_type=call_type,
                ticket_id=ticket_id,
                success=success,
                error=error,
            )
        except Exception:
            pass  # Never let logging break API calls

    async def _get_access_token(self) -> str:
        """Get fresh access token using refresh token"""
        if self.access_token:
            return self.access_token

        token_url = f"https://accounts.zoho.{self.data_center}/oauth/v2/token"

        data = {
            'refresh_token': self.settings.zoho_refresh_token,
            'client_id': self.settings.zoho_client_id,
            'client_secret': self.settings.zoho_client_secret,
            'grant_type': 'refresh_token'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                if response.status_code == 200:
                    self.access_token = response.json()['access_token']
                    self._log_zoho_call("oauth_token")
                    return self.access_token
                else:
                    self._log_zoho_call("oauth_token", success=False, error=f"HTTP {response.status_code}")
                    raise Exception(f"Failed to get access token: {response.text}")
        except Exception as e:
            if "Failed to get access token" not in str(e):
                self._log_zoho_call("oauth_token", success=False, error=str(e))
            raise

    async def _build_headers(self) -> Dict[str, str]:
        """Build authentication headers"""
        access_token = await self._get_access_token()

        return {
            "orgId": self.org_id,
            "Content-Type": "application/json",
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }

    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get ticket details by ID"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tickets/{ticket_id}",
                    headers=headers
                )
                response.raise_for_status()
                self._log_zoho_call("get_ticket", ticket_id=ticket_id)
                return response.json()
        except Exception as e:
            self._log_zoho_call("get_ticket", ticket_id=ticket_id, success=False, error=str(e))
            raise

    async def update_ticket(self, ticket_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket with new data"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/tickets/{ticket_id}",
                    headers=headers,
                    json=data
                )
                if response.status_code != 200:
                    logger.error(f"Failed to update ticket {ticket_id}: {response.status_code} - {response.text}")
                response.raise_for_status()
                self._log_zoho_call("update_ticket", ticket_id=ticket_id)
                return response.json()
        except Exception as e:
            self._log_zoho_call("update_ticket", ticket_id=ticket_id, success=False, error=str(e))
            raise

    async def add_tags(self, ticket_id: str, tags: List[str]) -> Dict[str, Any]:
        """Add tags to a ticket"""
        # Zoho Desk uses cf_ prefix for custom fields
        # We'll store tags in a custom multi-select field
        data = {
            "cf_ai_tags": ",".join(tags)
        }
        return await self.update_ticket(ticket_id, data)

    async def add_comment(self, ticket_id: str, content: str, is_public: bool = False) -> Dict[str, Any]:
        """Add a comment to a ticket"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tickets/{ticket_id}/comments",
                    headers=headers,
                    json={
                        "content": content,
                        "isPublic": is_public
                    }
                )
                response.raise_for_status()
                self._log_zoho_call("add_comment", ticket_id=ticket_id)
                return response.json()
        except Exception as e:
            self._log_zoho_call("add_comment", ticket_id=ticket_id, success=False, error=str(e))
            raise

    async def move_to_department(self, ticket_id: str, department_id: str) -> Dict[str, Any]:
        """Move ticket to a specific department/queue"""
        data = {
            "departmentId": department_id
        }
        return await self.update_ticket(ticket_id, data)

    async def list_tickets(self, limit: int = 50, _from: int = 0) -> List[Dict[str, Any]]:
        """List recent tickets (no search query required)"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tickets",
                    headers=headers,
                    params={"limit": limit, "from": _from, "sortBy": "createdTime"}
                )
                response.raise_for_status()
                self._log_zoho_call("list_tickets")
                return response.json().get("data", [])
        except Exception as e:
            self._log_zoho_call("list_tickets", success=False, error=str(e))
            raise

    async def search_tickets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tickets"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/tickets/search",
                    headers=headers,
                    params={
                        "searchStr": query,
                        "limit": limit
                    }
                )
                response.raise_for_status()
                self._log_zoho_call("search_tickets")
                return response.json().get("data", [])
        except Exception as e:
            self._log_zoho_call("search_tickets", success=False, error=str(e))
            raise

    async def get_departments(self) -> List[Dict[str, Any]]:
        """Get all departments"""
        try:
            headers = await self._build_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/departments",
                    headers=headers
                )
                response.raise_for_status()
                self._log_zoho_call("get_departments")
                return response.json().get("data", [])
        except Exception as e:
            self._log_zoho_call("get_departments", success=False, error=str(e))
            raise
