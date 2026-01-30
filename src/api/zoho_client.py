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
        self.headers = self._build_headers()
    
    def _build_headers(self) -> Dict[str, str]:
        """Build authentication headers"""
        headers = {
            "orgId": self.org_id,
            "Content-Type": "application/json"
        }
        
        if self.settings.zoho_api_token:
            headers["Authorization"] = f"Zoho-oauthtoken {self.settings.zoho_api_token}"
        elif self.settings.zoho_refresh_token:
            # TODO: Implement OAuth token refresh
            pass
        
        return headers
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Get ticket details by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tickets/{ticket_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def update_ticket(self, ticket_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update ticket with new data"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/tickets/{ticket_id}",
                headers=self.headers,
                json=data
            )
            if response.status_code != 200:
                logger.error(f"Failed to update ticket {ticket_id}: {response.status_code} - {response.text}")
            response.raise_for_status()
            return response.json()
    
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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tickets/{ticket_id}/comments",
                headers=self.headers,
                json={
                    "content": content,
                    "isPublic": is_public
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def move_to_department(self, ticket_id: str, department_id: str) -> Dict[str, Any]:
        """Move ticket to a specific department/queue"""
        data = {
            "departmentId": department_id
        }
        return await self.update_ticket(ticket_id, data)
    
    async def search_tickets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tickets"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tickets/search",
                headers=self.headers,
                params={
                    "searchStr": query,
                    "limit": limit
                }
            )
            response.raise_for_status()
            return response.json().get("data", [])
    
    async def get_departments(self) -> List[Dict[str, Any]]:
        """Get all departments"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/departments",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("data", [])
