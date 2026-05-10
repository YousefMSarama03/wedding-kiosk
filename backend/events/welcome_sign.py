"""
Dynamic welcome-sign copy for AI image prompts (side panel / easel in venue).

Text is derived from :class:`~events.models.Event` so generated photos can show a
natural, event-specific sign without hard-coding.
"""

from __future__ import annotations

import os

from events.models import Event

__all__ = [
    "welcome_sign_heading_for_event_type",
    "format_event_date_for_sign",
    "welcome_sign_prompt_block",
    "welcome_sign_extra_prompt",
]


def welcome_sign_heading_for_event_type(event_type: str) -> str:
    """Short title line for the sign (event-type specific)."""
    mapping = {
        Event.EVENT_TYPE_WEDDING: "Welcome Wedding",
        Event.EVENT_TYPE_HENNA: "Henna Night",
        Event.EVENT_TYPE_GRADUATION: "Graduation Celebration",
    }
    return mapping.get((event_type or "").strip(), "Celebration")


def format_event_date_for_sign(event: Event) -> str:
    """Human-readable date for signage (no leading zero on day)."""
    d = event.wedding_date
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _safe_quoted_name(raw: str, fallback: str) -> str:
    s = (raw or "").strip() or fallback
    return s.replace('"', "''")


def welcome_sign_prompt_block(event: Event) -> str:
    """
    Instruction block for image models: photorealistic side-panel sign with exact lines of text.
    """
    heading = welcome_sign_heading_for_event_type(event.event_type)
    a = _safe_quoted_name(event.bride_name, "Bride")
    b = _safe_quoted_name(event.groom_name, "Groom")
    date_line = format_event_date_for_sign(event)

    line2 = f'"{a}" & "{b}"'

    return f"""Welcome sign (side panel):
Include a photorealistic vertical welcome sign in the venue: a physical side panel or tall easel board at a natural side of the scene (not centered on the couple), with correct perspective, subtle stand shadow on the floor, and lighting consistent with the room (soft highlights on the board edge, no flat graphic overlay).

Materials that fit the event: painted wood, frosted acrylic, linen board, or printed foam-core; elegant event typography, not neon or cartoon.

The sign must show exactly three lines of text, readable in the photo, with these exact words and straight double quotes around the names as shown:
Line 1: {heading}
Line 2: {line2}
Line 3: {date_line}

Do not add extra words, logos, or different names on the sign. Do not replace quotation marks. Keep the sign secondary in the composition so the people remain the focus."""


def welcome_sign_extra_prompt(event: Event | None) -> str | None:
    """Returns prompt fragment if feature enabled and event given; otherwise ``None``."""
    if event is None:
        return None
    raw = os.getenv("KEEPSAKE_WELCOME_SIGN", "true").strip().lower()
    if raw in ("false", "0", "no", "off"):
        return None
    return welcome_sign_prompt_block(event)
