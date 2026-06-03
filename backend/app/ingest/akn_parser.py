"""
Parses Akoma Ntoso XML from the Oireachtas and extracts speech-level data.

The AKN namespace used is http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13.
Each element that represents spoken contribution (speech, question, answer,
continuation) is turned into a dict with the fields needed for SpeechChunk.
"""

import re
import logging
from lxml import etree

logger = logging.getLogger(__name__)

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13"
NS = {"akn": AKN_NS}

# Tags counted as speech contributions
SPEECH_TAGS = {"speech", "question", "answer", "continuation"}

# Very short procedural fragments we do not want (under this many chars)
MIN_TEXT_LEN = 40


def _text_of(el) -> str:
    parts = []
    for p in el.findall(".//akn:p", NS):
        raw = "".join(p.itertext()).strip()
        if raw:
            parts.append(raw)
    return " ".join(parts)


def _extract_speaker(el) -> tuple[str, str | None]:
    """
    Returns (speaker_name, role_string).

    Speaker names in this corpus are often verbose office titles with the
    actual name in parentheses, e.g.:
      "Minister of State at the Department of Finance (Deputy John Smith)"
    We extract "John Smith" as the name and keep the whole string as role.
    When there are no parentheses the whole string is the name and role is None.
    """
    # <from> child is the most reliable source
    from_el = el.find("akn:from", NS)
    raw = ""
    if from_el is not None:
        raw = "".join(from_el.itertext()).strip()

    if not raw:
        # Fall back to @by attribute, which looks like "#JohnSmith" or a URI
        by = el.get("by", "")
        raw = by.lstrip("#").replace("_", " ").strip()

    if not raw:
        return "Unknown", None

    # Try to pull the name out of parentheses
    m = re.search(r"\(([^)]+)\)$", raw)
    if m:
        inner = m.group(1).strip()
        # Strip titles: Deputy, Senator, Minister, An Taoiseach, etc.
        name = re.sub(
            r"^(Deputy|Senator|Minister|An |Aire |Teachta |Seanad[ó]ir)\s+",
            "",
            inner,
            flags=re.IGNORECASE,
        ).strip()
        # Keep the full raw as role if it contains more than just the name
        prefix = raw[: m.start()].strip().rstrip(",").strip()
        role = raw if prefix else None
        return name or inner, role

    # No parentheses — strip common standalone titles
    name = re.sub(
        r"^(Deputy|Senator|An Cathaoirleach|An Ceann Comhairle|An Leas-Cheann Comhairle|An Leas-Chathaoirleach)\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    return name or raw, None


def _section_heading(el) -> str | None:
    """Walk up the tree to find the enclosing debateSection heading."""
    parent = el.getparent()
    while parent is not None:
        local = etree.QName(parent.tag).localname if parent.tag else ""
        if local == "debateSection":
            h = parent.find("akn:heading", NS)
            if h is not None:
                return "".join(h.itertext()).strip() or None
        parent = parent.getparent()
    return None


def _member_uri(el) -> str | None:
    by = el.get("by", "")
    if by.startswith("http"):
        return by
    # Sometimes stored on <from>
    from_el = el.find("akn:from", NS)
    if from_el is not None:
        href = from_el.get("href") or from_el.get("refersTo", "")
        if href.startswith("http"):
            return href
    return None


def parse_debate_xml(
    xml_bytes: bytes,
    debate_date: str,
    chamber: str,
    debate_title: str,
    source_url: str,
) -> list[dict]:
    """
    Parse raw AKN XML bytes and return a list of speech dicts, one per
    contribution. Returns an empty list if parsing fails.
    """
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        logger.error("XML parse error for %s %s: %s", chamber, debate_date, e)
        return []

    # Confirm namespace is what we expect; warn if it drifted
    actual_ns = root.nsmap.get(None) or root.nsmap.get("akn", "")
    if actual_ns and actual_ns != AKN_NS:
        logger.warning(
            "Unexpected AKN namespace %r (expected %r); updating NS map for this file",
            actual_ns,
            AKN_NS,
        )
        # Update the NS dict temporarily for this parse so XPath still works
        NS["akn"] = actual_ns

    speeches = []
    seq = 0
    seen_ids: set[str] = set()

    for el in root.iter():
        local = etree.QName(el.tag).localname if el.tag else ""
        if local not in SPEECH_TAGS:
            continue

        text = _text_of(el)
        if len(text) < MIN_TEXT_LEN:
            continue

        speaker_name, role = _extract_speaker(el)
        topic = _section_heading(el)

        seq += 1
        speech_id = f"{chamber}:{debate_date}:{seq}"
        # Guard against duplicate IDs (shouldn't happen, but be safe)
        while speech_id in seen_ids:
            seq += 1
            speech_id = f"{chamber}:{debate_date}:{seq}"
        seen_ids.add(speech_id)

        speeches.append(
            {
                "speech_id": speech_id,
                "text": text,
                "speaker_name": speaker_name,
                "member_uri": _member_uri(el),
                "party": None,  # enriched later if available
                "role": role,
                "chamber": chamber,
                "debate_title": debate_title,
                "debate_date": debate_date,
                "topic_section": topic,
                "source_url": source_url,
            }
        )

    # Reset namespace back to default in case it was overridden above
    NS["akn"] = AKN_NS

    return speeches
