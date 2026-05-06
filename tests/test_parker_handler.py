"""
Unit tests for Parker the Parking Bot handler.

Fixtures are abridged versions of real Parker chat-thread HTML observed in
prod (channel=Chat, incoming ONLINE_CHAT thread `content` field).
"""
from src.services.parker_handler import (
    extract_customer_first_reply,
    is_parker_ticket,
    map_parker_intent,
    parse_parker_thread,
    transcript_to_text,
)


def _row(sender: str, msg: str, ts: str = "") -> str:
    """Build one Parker-style table row matching the real prod HTML structure."""
    label_cell = f'<td><div class="sender"><b>{sender}</b></div></td>'
    msg_cell = (
        f'<td><div style="float: right">{ts}</div>'
        f'<div style="float: left">{msg}</div></td>'
    )
    return f"<tr>{label_cell}{msg_cell}</tr>"


def _make_html(rows):
    return "<table>" + "".join(rows) + "</table>"


# ── Fixtures based on real Parker tickets ───────────────────────────────────

CANCEL_HTML = _make_html([
    _row("Question", "Purchasing/Cancelling a Permit"),
    _row("Parker, the Parking Bot", "Please select the option that best fits your situation.", "2:25 PM "),
    _row("Curtis", "I no longer need my permit."),
    _row("Parker, the Parking Bot", "If you no longer need your permit, please follow these steps to cancel."),
])

ADDITIONAL_HTML = _make_html([
    _row("Question", "Purchasing/Cancelling a Permit"),
    _row("Parker, the Parking Bot", "Please select the option that best fits your situation."),
    _row("Mendoza", "I need to purchase another permit."),
])

SOLD_OUT_HTML = _make_html([
    _row("Question", "Purchasing/Cancelling a Permit"),
    _row("Parker, the Parking Bot", "Please select the option."),
    _row("Curtis", "The permit that I need says it's sold out/reached my limit."),
])

VEHICLE_HTML = _make_html([
    _row("Question", "Edit Vehicle Info"),
    _row("Parker, the Parking Bot", "Ok, what would you like to edit?"),
    _row("Sanchez", "License Plate Number or State"),
])

PAYMENT_DOUBLE_HTML = _make_html([
    _row("Question", "Payment Issue"),
    _row("Parker, the Parking Bot", "Sorry to hear that. What issue are you experiencing?", "10:30 AM "),
    _row("Lee", "I was double charged."),
])

PAYMENT_UPDATE_HTML = _make_html([
    _row("Question", "Payment Issue"),
    _row("Parker, the Parking Bot", "Sorry to hear that. What issue are you experiencing?"),
    _row("Mendoza", "I need to update my payment method on file."),
])

LOGIN_HTML = _make_html([
    _row("Question", "Login/Account Issues"),
    _row("Parker, the Parking Bot", "Trouble accessing your account? Let me know more below!"),
    _row("Siebers", "I forgot my password."),
])

NOT_LISTED_HTML = _make_html([
    _row("Question", "Not Listed"),
    _row("Parker, the Parking Bot", "Sorry, what you need help with isn't listed."),
    _row("Smith", "I have a really weird billing situation that doesn't fit any category."),
])

# Pollution case: signature follows the customer's response in the thread.
SIGNATURE_NOISE_HTML = _make_html([
    _row("Question", "Edit Vehicle Info"),
    _row("Parker, the Parking Bot", "Ok, what would you like to edit?"),
    _row("Jones", "Thank you,Brandi W. ParkM Customer Support RepresentativeSupport: Support@parkm.com"),
    _row("Jones", "License Plate Number or State"),
])


# ── Detection ───────────────────────────────────────────────────────────────

class TestDetection:
    def test_chat_channel_is_parker(self):
        assert is_parker_ticket({"channel": "Chat"}) is True

    def test_email_channel_is_not_parker(self):
        assert is_parker_ticket({"channel": "Email"}) is False

    def test_web_channel_is_not_parker(self):
        assert is_parker_ticket({"channel": "Web"}) is False

    def test_missing_channel(self):
        assert is_parker_ticket({}) is False


# ── Parser ──────────────────────────────────────────────────────────────────

class TestParser:
    def test_basic_three_row_parse(self):
        rows = parse_parker_thread(CANCEL_HTML)
        assert rows[0] == ("Question", "Purchasing/Cancelling a Permit")
        assert rows[1][0] == "Parker, the Parking Bot"
        assert rows[2] == ("Curtis", "I no longer need my permit.")

    def test_strips_leading_timestamp(self):
        rows = parse_parker_thread(CANCEL_HTML)
        # Parker's row had "2:25 PM " prepended; the parser should drop it.
        assert "PM" not in rows[1][1][:6]
        assert rows[1][1].startswith("Please select")

    def test_empty_html_returns_empty(self):
        assert parse_parker_thread("") == []

    def test_malformed_html_does_not_crash(self):
        # Unclosed tag — html.parser is lenient; should return whatever it could.
        result = parse_parker_thread("<table><tr><td>x</td><td>y")
        assert isinstance(result, list)


# ── Customer first reply extraction ─────────────────────────────────────────

class TestFirstReply:
    def test_basic_extraction(self):
        rows = parse_parker_thread(CANCEL_HTML)
        assert extract_customer_first_reply(rows) == "I no longer need my permit."

    def test_skips_question_header_and_parker(self):
        rows = parse_parker_thread(VEHICLE_HTML)
        assert extract_customer_first_reply(rows) == "License Plate Number or State"

    def test_skips_signature_noise(self):
        rows = parse_parker_thread(SIGNATURE_NOISE_HTML)
        # Should skip the agent-signature row and pick the real reply.
        assert extract_customer_first_reply(rows) == "License Plate Number or State"

    def test_returns_none_on_no_reply(self):
        only_bot_html = _make_html([
            _row("Question", "Not Listed"),
            _row("Parker, the Parking Bot", "Sorry, that's not listed."),
        ])
        rows = parse_parker_thread(only_bot_html)
        assert extract_customer_first_reply(rows) is None


# ── Intent mapping ──────────────────────────────────────────────────────────

class TestIntentMap:
    def test_cancellation(self):
        assert (
            map_parker_intent("Purchasing/Cancelling a Permit", "I no longer need my permit.")
            == "Customer Canceling a Permit and Refunding"
        )

    def test_additional_permit(self):
        assert (
            map_parker_intent("Purchasing/Cancelling a Permit", "I need to purchase another permit.")
            == "Customer Inquiring for Additional Permit"
        )

    def test_locked_down(self):
        assert (
            map_parker_intent("Purchasing/Cancelling a Permit", "The permit that I need says it's sold out/reached my limit.")
            == "Customer Inquiring for Locked Down Permit"
        )

    def test_vehicle_update_plate(self):
        assert (
            map_parker_intent("Edit Vehicle Info", "License Plate Number or State")
            == "Customer Update Vehicle Info"
        )

    def test_vehicle_update_vin(self):
        assert (
            map_parker_intent("Edit Vehicle Info", "Last 6 of VIN")
            == "Customer Update Vehicle Info"
        )

    def test_payment_double_charged(self):
        assert (
            map_parker_intent("Payment Issue", "I was double charged.")
            == "Customer Double Charged or Extra Charges"
        )

    def test_payment_method_update(self):
        assert (
            map_parker_intent("Payment Issue", "I need to update my payment method on file.")
            == "Customer Payment Help"
        )

    def test_password_reset(self):
        assert (
            map_parker_intent("Login/Account Issues", "I forgot my password.")
            == "Customer Password Reset"
        )

    def test_not_listed_returns_none(self):
        assert (
            map_parker_intent("Not Listed", "I have a really weird billing situation.")
            is None
        )

    def test_unknown_subject_returns_none(self):
        assert map_parker_intent("Some Future Menu", "anything") is None

    def test_unmatched_reply_returns_none(self):
        # Subject has rules, but the reply doesn't trigger any of them.
        assert (
            map_parker_intent("Login/Account Issues", "I want to delete my account permanently.")
            is None
        )

    def test_none_reply_returns_none(self):
        assert map_parker_intent("Edit Vehicle Info", None) is None


# ── Transcript rendering ────────────────────────────────────────────────────

class TestTranscriptText:
    def test_includes_sender_labels(self):
        rows = parse_parker_thread(CANCEL_HTML)
        text = transcript_to_text(rows)
        assert "[Parker, the Parking Bot]" in text
        assert "[Curtis]" in text
        assert "I no longer need my permit." in text

    def test_drops_signature_noise(self):
        rows = parse_parker_thread(SIGNATURE_NOISE_HTML)
        text = transcript_to_text(rows)
        assert "ParkM Customer Support" not in text
        assert "License Plate Number or State" in text


# ── End-to-end parse + map ──────────────────────────────────────────────────

class TestEndToEnd:
    """Subject + parsed transcript -> deterministic tag, all in one pass."""

    def test_cancel_flow(self):
        rows = parse_parker_thread(CANCEL_HTML)
        reply = extract_customer_first_reply(rows)
        assert (
            map_parker_intent("Purchasing/Cancelling a Permit", reply)
            == "Customer Canceling a Permit and Refunding"
        )

    def test_payment_flow(self):
        rows = parse_parker_thread(PAYMENT_DOUBLE_HTML)
        reply = extract_customer_first_reply(rows)
        assert (
            map_parker_intent("Payment Issue", reply)
            == "Customer Double Charged or Extra Charges"
        )

    def test_login_flow(self):
        rows = parse_parker_thread(LOGIN_HTML)
        reply = extract_customer_first_reply(rows)
        assert (
            map_parker_intent("Login/Account Issues", reply)
            == "Customer Password Reset"
        )

    def test_not_listed_falls_through(self):
        rows = parse_parker_thread(NOT_LISTED_HTML)
        reply = extract_customer_first_reply(rows)
        assert map_parker_intent("Not Listed", reply) is None
