import importlib
from types import SimpleNamespace

import pytest


class FakeZohoClient:
    def __init__(self):
        self.ticket = {
            "id": "T1",
            "subject": "Cancelar",
            "description": "",
            "email": "customer@example.com",
            "departmentId": "D1",
            "cf": {},
        }

    async def get_ticket(self, ticket_id):
        assert ticket_id == "T1"
        return self.ticket

    async def list_threads(self, ticket_id, limit=10):
        assert ticket_id == "T1"
        return [
            {
                "id": "agent-reply",
                "direction": "out",
                "createdTime": "2026-05-19T09:00:00Z",
            },
            {
                "id": "customer-original",
                "direction": "in",
                "createdTime": "2026-05-19T08:00:00Z",
            },
        ]

    async def get_thread_content(self, ticket_id, thread_id):
        assert ticket_id == "T1"
        assert thread_id == "customer-original"
        return {
            "content": (
                "<p>Hola buen dia deseo cancelar la suscripcion de la "
                "2012 Nissan Rogue Burgundy UT-791010.</p>"
            )
        }


class FakeClassifier:
    def __init__(self):
        self.calls = []

    def classify_email(self, subject, body, from_email="", ticket_id="", department_id=None):
        self.calls.append(
            {
                "subject": subject,
                "body": body,
                "from_email": from_email,
                "ticket_id": ticket_id,
                "department_id": department_id,
            }
        )
        return {
            "tags": ["Customer Canceling a Permit and Refunding"],
            "intent": "Customer Canceling a Permit and Refunding",
            "complexity": "simple",
            "language": "spanish",
            "urgency": "medium",
            "confidence": 0.9,
            "key_entities": {"license_plate": "791010"},
        }

    def get_routing_recommendation(self, classification):
        return "Quick Updates"


class FakeTagger:
    async def apply_classification_tags(self, ticket_id, classification, routing):
        return True


@pytest.mark.asyncio
async def test_webhook_uses_initial_inbound_thread_when_description_is_empty(monkeypatch):
    monkeypatch.setenv("ZOHO_ORG_ID", "test-org")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DEBUG", "true")

    webhooks = importlib.import_module("src.api.webhooks")
    fake_classifier = FakeClassifier()

    monkeypatch.setattr(webhooks, "zoho_client", FakeZohoClient())
    monkeypatch.setattr(webhooks, "classifier", fake_classifier)
    monkeypatch.setattr(webhooks, "tagger", FakeTagger())

    async def fake_prepare_parker_ticket(zoho_client, ticket_data):
        return SimpleNamespace(is_parker=False, transcript_text="", deterministic_tag=None)

    monkeypatch.setattr(webhooks, "prepare_parker_ticket", fake_prepare_parker_ticket)

    await webhooks.process_ticket_webhook("T1", {})

    assert len(fake_classifier.calls) == 1
    body = fake_classifier.calls[0]["body"]
    assert "UT-791010" in body
    assert "<p>" not in body
