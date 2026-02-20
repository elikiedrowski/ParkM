"""
Unit tests for the Wizard service.
Tests intent lookup, placeholder substitution, and fallback behavior.
"""
import pytest
from src.services.wizard import (
    get_wizard_for_intent,
    list_intents,
    list_templates,
    _fill_placeholders,
)

ALL_INTENTS = [
    "refund_request", "permit_cancellation", "account_update", "payment_issue",
    "permit_inquiry", "move_out", "technical_issue", "tow_issue",
    "password_reset", "general_question", "unclear",
]


class TestListIntents:
    def test_all_11_intents_present(self):
        intents = list_intents()
        for intent in ALL_INTENTS:
            assert intent in intents, f"Missing intent: {intent}"

    def test_no_comment_keys(self):
        intents = list_intents()
        for i in intents:
            assert not i.startswith("_"), f"Private key leaked: {i}"

    def test_new_intents_present(self):
        intents = list_intents()
        assert "tow_issue" in intents
        assert "password_reset" in intents


class TestGetWizardForIntent:
    def test_returns_wizard_for_every_intent(self):
        for intent in ALL_INTENTS:
            wizard = get_wizard_for_intent(intent)
            assert "steps" in wizard, f"No steps for intent: {intent}"
            assert len(wizard["steps"]) > 0, f"Empty steps for intent: {intent}"

    def test_unknown_intent_falls_back_to_unclear(self):
        wizard = get_wizard_for_intent("nonexistent_intent")
        assert wizard["label"] == "Unclear / Needs Review"

    def test_wizard_has_required_fields(self):
        wizard = get_wizard_for_intent("refund_request")
        assert "label" in wizard
        assert "icon" in wizard
        assert "color" in wizard
        assert "intro" in wizard
        assert "steps" in wizard
        assert "quick_templates" in wizard

    def test_entity_placeholder_substituted_when_provided(self):
        classification = {
            "key_entities": {
                "license_plate": "ABC-1234",
                "move_out_date": "2026-01-15",
                "amount": None,
            }
        }
        wizard = get_wizard_for_intent("refund_request", classification)
        substeps = [
            s.get("substep", "")
            for s in wizard["steps"]
            if s.get("substep")
        ]
        all_substeps = " ".join(substeps)
        assert "ABC-1234" in all_substeps
        assert "2026-01-15" in all_substeps

    def test_missing_entity_shows_not_found_message(self):
        wizard = get_wizard_for_intent("refund_request", classification=None)
        substeps = [s.get("substep", "") for s in wizard["steps"] if s.get("substep")]
        all_substeps = " ".join(substeps)
        assert "Not Found in Email" in all_substeps

    def test_entity_found_flag_set_correctly(self):
        classification = {
            "key_entities": {"license_plate": "XYZ-9999", "move_out_date": None}
        }
        wizard = get_wizard_for_intent("permit_cancellation", classification)
        plate_step = next(
            (s for s in wizard["steps"] if s.get("entity_field") == "license_plate"),
            None,
        )
        assert plate_step is not None
        assert plate_step["entity_found"] is True
        assert plate_step["entity_value"] == "XYZ-9999"

    def test_confidence_attached_when_classification_provided(self):
        classification = {
            "confidence": 0.87,
            "requires_human_review": False,
            "key_entities": {},
        }
        wizard = get_wizard_for_intent("permit_inquiry", classification)
        assert wizard["ai_confidence"] == 0.87

    def test_deep_copy_prevents_mutation(self):
        w1 = get_wizard_for_intent("refund_request")
        w2 = get_wizard_for_intent("refund_request")
        w1["steps"][0]["text"] = "MUTATED"
        assert w2["steps"][0]["text"] != "MUTATED"

    def test_tow_issue_wizard_has_decision_point(self):
        wizard = get_wizard_for_intent("tow_issue")
        decision_steps = [s for s in wizard["steps"] if s.get("decision_point")]
        assert len(decision_steps) >= 1

    def test_password_reset_wizard_has_5_steps(self):
        wizard = get_wizard_for_intent("password_reset")
        assert len(wizard["steps"]) == 5

    def test_extracted_entities_key_also_accepted(self):
        """Classifier sometimes returns 'extracted_entities' instead of 'key_entities'."""
        classification = {
            "extracted_entities": {"license_plate": "DEF-5678"},
        }
        wizard = get_wizard_for_intent("account_update", classification)
        substeps = [s.get("substep", "") for s in wizard["steps"] if s.get("substep")]
        assert "DEF-5678" in " ".join(substeps)


class TestFillPlaceholders:
    def test_replaces_known_entity(self):
        result = _fill_placeholders("Plate: {{license_plate}}", {"license_plate": "ABC-123"})
        assert result == "Plate: ABC-123"

    def test_replaces_multiple_entities(self):
        result = _fill_placeholders(
            "{{license_plate}} moved out on {{move_out_date}}",
            {"license_plate": "XYZ", "move_out_date": "2026-01-01"},
        )
        assert result == "XYZ moved out on 2026-01-01"

    def test_unfilled_placeholder_becomes_readable_label(self):
        result = _fill_placeholders("Plate: {{license_plate}}", {})
        assert "Not Found in Email" in result
        assert "License Plate" in result

    def test_no_placeholders_unchanged(self):
        text = "Search parkm.app by customer email address"
        assert _fill_placeholders(text, {}) == text


class TestListTemplates:
    def test_returns_html_files(self):
        templates = list_templates()
        assert len(templates) >= 12
        for t in templates:
            assert t.endswith(".html")

    def test_expected_templates_present(self):
        templates = list_templates()
        expected = [
            "refund_approved.html",
            "refund_denied_outside_window.html",
            "missing_license_plate.html",
            "missing_move_out_date.html",
            "cancellation_confirmed.html",
            "general_inquiry_response.html",
        ]
        for t in expected:
            assert t in templates, f"Missing template: {t}"
