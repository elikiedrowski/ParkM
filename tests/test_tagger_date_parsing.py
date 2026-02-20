"""
Unit tests for TicketTagger date parsing logic.
Tests _parse_date() without making any Zoho API calls.
"""
import pytest
from src.services.tagger import TicketTagger


@pytest.fixture
def tagger():
    return TicketTagger.__new__(TicketTagger)


class TestDateParsing:
    """Tests for _parse_date()"""

    def test_full_month_name(self, tagger):
        assert tagger._parse_date("January 1, 2026") == "2026-01-01"

    def test_full_month_with_ordinal_st(self, tagger):
        assert tagger._parse_date("January 1st, 2026") == "2026-01-01"

    def test_full_month_with_ordinal_nd(self, tagger):
        assert tagger._parse_date("February 2nd, 2026") == "2026-02-02"

    def test_full_month_with_ordinal_rd(self, tagger):
        assert tagger._parse_date("March 3rd, 2026") == "2026-03-03"

    def test_full_month_with_ordinal_th(self, tagger):
        assert tagger._parse_date("April 15th, 2026") == "2026-04-15"

    def test_abbreviated_month(self, tagger):
        assert tagger._parse_date("Jan 1, 2026") == "2026-01-01"

    def test_slash_format(self, tagger):
        assert tagger._parse_date("01/15/2026") == "2026-01-15"

    def test_iso_format_passthrough(self, tagger):
        assert tagger._parse_date("2026-01-01") == "2026-01-01"

    def test_dash_format(self, tagger):
        assert tagger._parse_date("15-01-2026") == "2026-01-15"

    def test_unparseable_returns_none(self, tagger):
        assert tagger._parse_date("next month") is None

    def test_empty_string_returns_none(self, tagger):
        assert tagger._parse_date("") is None

    def test_garbage_returns_none(self, tagger):
        assert tagger._parse_date("asdfghjkl") is None

    def test_end_of_year(self, tagger):
        assert tagger._parse_date("December 31st, 2025") == "2025-12-31"
