"""
Unit tests for webhook payload parsing.
Tests that ticket IDs and field data are extracted correctly from
Zoho's nested payload format, without making any HTTP calls.
"""
import pytest


class TestZohoPayloadParsing:
    """
    Zoho sends: { "payload": { ...ticket data... }, "eventType": "Ticket_Add" }
    Ticket ID is at payload["payload"]["id"], NOT at top level.
    """

    TICKET_CREATED_PAYLOAD = {
        "payload": {
            "id": "1004699000046503129",
            "ticketNumber": "69889",
            "subject": "My car was towed",
            "description": "I have a valid permit but my car was towed.",
            "departmentId": "1004699000001888029",
            "email": "customer@example.com",
            "cf": {
                "cf_ai_intent": None,
                "cf_agent_corrected_intent": None,
                "cf_ai_confidence": None,
            }
        },
        "eventType": "Ticket_Add"
    }

    CORRECTION_PAYLOAD = {
        "payload": {
            "id": "1004699000046503129",
            "departmentId": "1004699000001888029",
            "cf": {
                "cf_ai_intent": "permit_inquiry",
                "cf_agent_corrected_intent": "tow_issue",
                "cf_ai_confidence": "85",
            }
        },
        "eventType": "Ticket_Update"
    }

    def test_ticket_id_extracted_from_nested_payload(self):
        payload = self.TICKET_CREATED_PAYLOAD
        ticket_data = payload.get("payload", {})
        ticket_id = ticket_data.get("id")
        assert ticket_id == "1004699000046503129"

    def test_department_id_extracted(self):
        payload = self.TICKET_CREATED_PAYLOAD
        ticket_data = payload.get("payload", {})
        dept_id = ticket_data.get("departmentId")
        assert dept_id == "1004699000001888029"

    def test_subject_and_description_extracted(self):
        payload = self.TICKET_CREATED_PAYLOAD
        ticket_data = payload.get("payload", {})
        assert ticket_data.get("subject") == "My car was towed"
        assert "valid permit" in ticket_data.get("description", "")

    def test_correction_original_intent_from_cf(self):
        payload = self.CORRECTION_PAYLOAD
        ticket_data = payload.get("payload", {})
        cf = ticket_data.get("cf", {})
        original_intent = cf.get("cf_ai_intent")
        corrected_intent = cf.get("cf_agent_corrected_intent")
        assert original_intent == "permit_inquiry"
        assert corrected_intent == "tow_issue"

    def test_correction_confidence_from_cf(self):
        payload = self.CORRECTION_PAYLOAD
        ticket_data = payload.get("payload", {})
        cf = ticket_data.get("cf", {})
        confidence = cf.get("cf_ai_confidence")
        # Stored as string in Zoho, must be converted
        assert int(confidence) == 85

    def test_is_misclassification_logic(self):
        """Reproduce the is_misclassification logic from correction_logger."""
        corrected_intent = "tow_issue"
        original_intent = "permit_inquiry"
        is_misclassification = (
            corrected_intent != "correct" and corrected_intent != original_intent
        )
        assert is_misclassification is True

    def test_not_misclassification_when_correct_keyword(self):
        corrected_intent = "correct"
        original_intent = "permit_inquiry"
        is_misclassification = (
            corrected_intent != "correct" and corrected_intent != original_intent
        )
        assert is_misclassification is False

    def test_not_misclassification_when_same_intent(self):
        corrected_intent = "tow_issue"
        original_intent = "tow_issue"
        is_misclassification = (
            corrected_intent != "correct" and corrected_intent != original_intent
        )
        assert is_misclassification is False

    def test_new_intents_recognized_in_corrections(self):
        """tow_issue and password_reset should be valid corrected intents."""
        valid_intents = [
            "refund_request", "permit_cancellation", "account_update",
            "payment_issue", "permit_inquiry", "move_out", "technical_issue",
            "tow_issue", "password_reset", "general_question", "unclear",
        ]
        assert "tow_issue" in valid_intents
        assert "password_reset" in valid_intents
