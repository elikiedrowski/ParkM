"""
Unit tests for the correction logger.
Tests logging logic and accuracy calculations without touching real files
by using a temporary directory.
"""
import json
import os
import pytest
import tempfile
from unittest.mock import patch


class TestLogCorrection:
    def test_logs_misclassification(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import log_correction
            result = log_correction(
                ticket_id="T001",
                original_intent="permit_inquiry",
                corrected_intent="refund_request",
                confidence=75,
                department_id="1234",
            )

        assert result is True
        with open(log_file) as f:
            entry = json.loads(f.readline())

        assert entry["ticket_id"] == "T001"
        assert entry["original_intent"] == "permit_inquiry"
        assert entry["corrected_intent"] == "refund_request"
        assert entry["is_misclassification"] is True
        assert entry["confidence"] == 75
        assert entry["department_id"] == "1234"

    def test_correct_classification_not_marked_misclassification(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import log_correction
            log_correction(
                ticket_id="T002",
                original_intent="refund_request",
                corrected_intent="correct",
                confidence=90,
            )

        with open(log_file) as f:
            entry = json.loads(f.readline())

        assert entry["is_misclassification"] is False

    def test_same_intent_not_misclassification(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import log_correction
            log_correction(
                ticket_id="T003",
                original_intent="refund_request",
                corrected_intent="refund_request",
                confidence=80,
            )

        with open(log_file) as f:
            entry = json.loads(f.readline())

        assert entry["is_misclassification"] is False


class TestGetCorrectionsSummary:
    def _write_corrections(self, log_file, entries):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")

    def test_empty_file_returns_zeros(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import get_corrections_summary
            result = get_corrections_summary()
        assert result["total"] == 0
        assert result["misclassifications"] == 0

    def test_accuracy_rate_calculation(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        entries = [
            {"original_intent": "refund_request", "corrected_intent": "correct", "is_misclassification": False},
            {"original_intent": "permit_inquiry", "corrected_intent": "refund_request", "is_misclassification": True},
            {"original_intent": "payment_issue", "corrected_intent": "correct", "is_misclassification": False},
            {"original_intent": "account_update", "corrected_intent": "correct", "is_misclassification": False},
        ]
        self._write_corrections(log_file, entries)
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import get_corrections_summary
            result = get_corrections_summary()

        assert result["total"] == 4
        assert result["misclassifications"] == 1
        assert result["accuracy_rate"] == 75.0

    def test_confusion_pairs_ranked_by_frequency(self, tmp_path):
        log_file = str(tmp_path / "corrections.jsonl")
        entries = [
            {"original_intent": "permit_inquiry", "corrected_intent": "refund_request", "is_misclassification": True},
            {"original_intent": "permit_inquiry", "corrected_intent": "refund_request", "is_misclassification": True},
            {"original_intent": "payment_issue", "corrected_intent": "tow_issue", "is_misclassification": True},
        ]
        self._write_corrections(log_file, entries)
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import get_corrections_summary
            result = get_corrections_summary()

        pairs = result["confusion_pairs"]
        assert pairs[0]["pair"] == "permit_inquiry → refund_request"
        assert pairs[0]["count"] == 2
        assert pairs[1]["pair"] == "payment_issue → tow_issue"

    def test_new_intents_in_confusion_pairs(self, tmp_path):
        """Ensure tow_issue and password_reset appear correctly in confusion pairs."""
        log_file = str(tmp_path / "corrections.jsonl")
        entries = [
            {"original_intent": "technical_issue", "corrected_intent": "tow_issue", "is_misclassification": True},
            {"original_intent": "technical_issue", "corrected_intent": "password_reset", "is_misclassification": True},
        ]
        self._write_corrections(log_file, entries)
        with patch("src.services.correction_logger.CORRECTIONS_LOG", log_file):
            from src.services.correction_logger import get_corrections_summary
            result = get_corrections_summary()

        pair_names = [p["pair"] for p in result["confusion_pairs"]]
        assert "technical_issue → tow_issue" in pair_names
        assert "technical_issue → password_reset" in pair_names
