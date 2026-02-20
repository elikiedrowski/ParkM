"""
Unit tests for EmailClassifier routing logic.
Tests the get_routing_recommendation() method without making any OpenAI API calls.
"""
import pytest
from src.services.classifier import EmailClassifier


@pytest.fixture
def classifier():
    # We only test get_routing_recommendation(), which requires no API key
    return EmailClassifier.__new__(EmailClassifier)


class TestRoutingRecommendation:
    """Tests for get_routing_recommendation()"""

    def test_simple_refund_routes_to_auto_resolution(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "refund_request", "complexity": "simple", "urgency": "medium"}
        )
        assert result == "Auto-Resolution Queue"

    def test_complex_refund_routes_to_accounting(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "refund_request", "complexity": "complex", "urgency": "medium"}
        )
        assert result == "Accounting/Refunds"

    def test_payment_issue_routes_to_accounting(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "payment_issue", "complexity": "simple", "urgency": "medium"}
        )
        assert result == "Accounting/Refunds"

    def test_simple_permit_cancellation_routes_to_quick_updates(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "permit_cancellation", "complexity": "simple", "urgency": "low"}
        )
        assert result == "Quick Updates"

    def test_complex_permit_cancellation_routes_to_escalations(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "permit_cancellation", "complexity": "complex", "urgency": "medium"}
        )
        assert result == "Escalations"

    def test_simple_account_update_routes_to_quick_updates(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "account_update", "complexity": "simple", "urgency": "low"}
        )
        assert result == "Quick Updates"

    def test_tow_issue_always_routes_to_escalations(self, classifier):
        for complexity in ["simple", "moderate", "complex"]:
            result = classifier.get_routing_recommendation(
                {"intent": "tow_issue", "complexity": complexity, "urgency": "medium"}
            )
            assert result == "Escalations", f"tow_issue/{complexity} should route to Escalations"

    def test_tow_issue_high_urgency_still_escalations(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "tow_issue", "complexity": "simple", "urgency": "high"}
        )
        assert result == "Escalations"

    def test_password_reset_routes_to_quick_updates(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "password_reset", "complexity": "simple", "urgency": "low"}
        )
        assert result == "Quick Updates"

    def test_high_urgency_routes_to_escalations(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "permit_inquiry", "complexity": "simple", "urgency": "high"}
        )
        assert result == "Escalations"

    def test_complex_ticket_routes_to_escalations(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "general_question", "complexity": "complex", "urgency": "low"}
        )
        assert result == "Escalations"

    def test_general_question_routes_to_general_support(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "general_question", "complexity": "simple", "urgency": "low"}
        )
        assert result == "General Support"

    def test_unclear_routes_to_general_support(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "unclear", "complexity": "simple", "urgency": "low"}
        )
        assert result == "General Support"

    def test_permit_inquiry_routes_to_general_support(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "permit_inquiry", "complexity": "moderate", "urgency": "medium"}
        )
        assert result == "General Support"

    def test_move_out_routes_to_general_support(self, classifier):
        result = classifier.get_routing_recommendation(
            {"intent": "move_out", "complexity": "simple", "urgency": "low"}
        )
        assert result == "General Support"
