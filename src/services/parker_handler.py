"""
Parker the Parking Bot ticket handler.

Parker is ParkM's website chatbot. It creates Zoho tickets via the Chat channel
with an empty `description` — the conversation is in a structured HTML table
inside the incoming chat thread (channel=ONLINE_CHAT, direction=in).

Without this handler the classifier sees empty text and tags ~22% of incoming
tickets as "Needs Tag" at 30% confidence. With it we parse the transcript,
deterministically tag the predictable cases (subject + customer first reply ->
canonical tag), and feed a clean text rendering to the LLM for everything else.
"""
import logging
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Detection ────────────────────────────────────────────────────────────────

PARKER_CHANNEL = "Chat"


def is_parker_ticket(ticket: Dict[str, Any]) -> bool:
    """True if the ticket came from Parker (channel == 'Chat')."""
    return ticket.get("channel") == PARKER_CHANNEL


# ── HTML parsing ────────────────────────────────────────────────────────────

_TIMESTAMP_PREFIX_RE = re.compile(
    r"^\s*(?:\d{1,2}\s+\w+,\s*)?\d{1,2}:\d{2}\s*[AP]M\s*", re.IGNORECASE
)

_SUPPORT_SIG_HINTS = (
    "parkm customer support",
    "support@parkm.com",
    "parkm.app",
    "where convenience meets control",
)


def _strip_timestamp(msg: str) -> str:
    return _TIMESTAMP_PREFIX_RE.sub("", msg).strip()


def _is_signature_noise(msg: str) -> bool:
    low = msg.lower()
    return any(h in low for h in _SUPPORT_SIG_HINTS)


class _RowParser(HTMLParser):
    """Walks Parker's HTML table and emits (sender_label, message_text) tuples."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: List[Tuple[str, str]] = []
        self._cells: List[str] = []
        self._cell_text: List[str] = []
        self._in_td: bool = False

    def handle_starttag(self, tag: str, attrs):
        if tag == "tr":
            self._cells = []
        elif tag == "td":
            self._in_td = True
            self._cell_text = []

    def handle_endtag(self, tag: str):
        if tag == "td":
            self._in_td = False
            text = " ".join("".join(self._cell_text).split()).strip()
            self._cells.append(text)
        elif tag == "tr" and len(self._cells) >= 2:
            sender = self._cells[0]
            msg = _strip_timestamp(self._cells[-1])
            self.rows.append((sender, msg))

    def handle_data(self, data: str):
        if self._in_td:
            self._cell_text.append(data)


def parse_parker_thread(html: str) -> List[Tuple[str, str]]:
    """Parse Parker's HTML transcript into [(sender, message), ...] rows."""
    if not html:
        return []
    p = _RowParser()
    try:
        p.feed(html)
    except Exception as e:
        logger.warning(f"Parker HTML parser failed: {e}")
        return []
    return p.rows


def extract_customer_first_reply(rows: List[Tuple[str, str]]) -> Optional[str]:
    """First substantive reply from the resident (skipping Parker, Question header,
    signature noise, empty cells)."""
    for sender, msg in rows:
        if not msg:
            continue
        sender_norm = sender.strip().upper()
        if "PARKER" in sender_norm or sender_norm == "QUESTION":
            continue
        if _is_signature_noise(msg):
            continue
        return msg
    return None


def transcript_to_text(rows: List[Tuple[str, str]]) -> str:
    """Render parsed rows as a clean plain-text block suitable for LLM input.

    Skips signature noise. Preserves the Parker/customer turn structure so the
    LLM can read it like a script.
    """
    lines: List[str] = []
    for sender, msg in rows:
        if not msg or _is_signature_noise(msg):
            continue
        if sender:
            lines.append(f"[{sender}] {msg}")
        else:
            lines.append(msg)
    return "\n".join(lines)


# ── Deterministic intent mapping ─────────────────────────────────────────────

# Subject (Parker's top-level menu) -> ordered (substring_in_first_reply, canonical_tag).
# First match wins. Substring match is case-insensitive. Tags must exist in
# src/wizard/tagging_values.json — all listed below were verified at the time
# this handler was added.
_PARKER_INTENT_MAP: Dict[str, List[Tuple[str, str]]] = {
    "Purchasing/Cancelling a Permit": [
        ("no longer need", "Customer Canceling a Permit and Refunding"),
        ("cancel", "Customer Canceling a Permit and Refunding"),
        ("purchase another", "Customer Inquiring for Additional Permit"),
        ("additional permit", "Customer Inquiring for Additional Permit"),
        ("sold out", "Customer Inquiring for Locked Down Permit"),
        ("limit reached", "Customer Inquiring for Locked Down Permit"),
        ("locked down", "Customer Inquiring for Locked Down Permit"),
        ("buying", "Customer Need help buying a permit"),
        ("first permit", "Customer Need help buying a permit"),
        ("new resident", "Customer Need help buying a permit"),
    ],
    "Edit Vehicle Info": [
        ("license plate", "Customer Update Vehicle Info"),
        ("plate number", "Customer Update Vehicle Info"),
        ("vin", "Customer Update Vehicle Info"),
        ("vehicle", "Customer Update Vehicle Info"),
        ("state", "Customer Update Vehicle Info"),
    ],
    "Payment Issue": [
        ("double", "Customer Double Charged or Extra Charges"),
        ("twice", "Customer Double Charged or Extra Charges"),
        ("extra charge", "Customer Double Charged or Extra Charges"),
        ("update", "Customer Payment Help"),
        ("payment method", "Customer Payment Help"),
        ("unpaid", "Customer Payment Help"),
        ("balance", "Customer Payment Help"),
        ("can't pay", "Customer Payment Help"),
        ("cant pay", "Customer Payment Help"),
    ],
    "Login/Account Issues": [
        ("forgot password", "Customer Password Reset"),
        ("password", "Customer Password Reset"),
        ("reset", "Customer Password Reset"),
        ("can't log", "Customer Password Reset"),
        ("cant log", "Customer Password Reset"),
        ("locked out", "Customer Password Reset"),
    ],
    # "Not Listed" intentionally has no rules — falls through to LLM.
}


def map_parker_intent(subject: str, customer_reply: Optional[str]) -> Optional[str]:
    """Return a canonical tag for a Parker ticket, or None if no rule matches."""
    if not customer_reply:
        return None
    rules = _PARKER_INTENT_MAP.get(subject, [])
    reply_lower = customer_reply.lower()
    for needle, tag in rules:
        if needle in reply_lower:
            return tag
    return None


# ── Top-level orchestration ──────────────────────────────────────────────────

class ParkerContext:
    """Result of preparing a Parker ticket for classification.

    Attributes:
        is_parker: True if this ticket was identified as Parker-generated.
        transcript_text: Parsed Q&A rendered as plain text. Empty if not Parker
            or if parsing failed. Use this in place of the (empty) ticket
            description when calling the classifier.
        deterministic_tag: Canonical tag from the lookup table, or None if no
            rule matched. When set, the classifier's tag output should be
            overridden with this value at high confidence.
        customer_first_reply: The resident's first substantive turn (debug aid).
    """

    __slots__ = ("is_parker", "transcript_text", "deterministic_tag", "customer_first_reply")

    def __init__(
        self,
        is_parker: bool,
        transcript_text: str = "",
        deterministic_tag: Optional[str] = None,
        customer_first_reply: Optional[str] = None,
    ):
        self.is_parker = is_parker
        self.transcript_text = transcript_text
        self.deterministic_tag = deterministic_tag
        self.customer_first_reply = customer_first_reply


async def prepare_parker_ticket(zoho_client, ticket: Dict[str, Any]) -> ParkerContext:
    """If `ticket` came from Parker, fetch and parse the chat transcript.

    Returns a `ParkerContext` describing what we were able to extract.
    Never raises — all errors are logged and surfaced as a "not parker" or
    "no transcript" context so the caller can fall back to existing behavior.
    """
    if not is_parker_ticket(ticket):
        return ParkerContext(is_parker=False)

    ticket_id = ticket.get("id")
    subject = ticket.get("subject", "") or ""

    try:
        threads = await zoho_client.list_threads(ticket_id)
    except Exception as e:
        logger.warning(f"[{ticket_id}] Parker: failed to list threads: {e}")
        return ParkerContext(is_parker=True)

    incoming = next(
        (t for t in threads if t.get("direction") == "in" and t.get("channel") == "ONLINE_CHAT"),
        None,
    )
    if incoming is None:
        # Some Parker tickets have only outbound agent threads. Fall through.
        logger.info(f"[{ticket_id}] Parker: no incoming ONLINE_CHAT thread")
        return ParkerContext(is_parker=True)

    try:
        thread_detail = await zoho_client.get_thread_content(ticket_id, incoming["id"])
    except Exception as e:
        logger.warning(f"[{ticket_id}] Parker: failed to fetch thread content: {e}")
        return ParkerContext(is_parker=True)

    html = thread_detail.get("content") or ""
    rows = parse_parker_thread(html)
    if not rows:
        logger.info(f"[{ticket_id}] Parker: parser returned 0 rows")
        return ParkerContext(is_parker=True)

    customer_reply = extract_customer_first_reply(rows)
    deterministic_tag = map_parker_intent(subject, customer_reply)
    transcript_text = transcript_to_text(rows)

    logger.info(
        f"[{ticket_id}] Parker: subject={subject!r} first_reply={customer_reply!r} "
        f"deterministic_tag={deterministic_tag!r}"
    )

    return ParkerContext(
        is_parker=True,
        transcript_text=transcript_text,
        deterministic_tag=deterministic_tag,
        customer_first_reply=customer_reply,
    )
