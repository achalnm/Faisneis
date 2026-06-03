import re
import logging
from lxml import etree

logger = logging.getLogger(__name__)

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0/CSD13"
NS = {"akn": AKN_NS}

SPEECH_TAGS = {"speech", "question", "answer", "continuation"}
MIN_TEXT_LEN = 40


def _text_of(el) -> str:
    parts = []
    for p in el.findall(".//akn:p", NS):
        raw = "".join(p.itertext()).strip()
        if raw:
            parts.append(raw)
    return " ".join(parts)


def _extract_speaker(el) -> tuple[str, str | None]:
    from_el = el.find("akn:from", NS)
    raw = ""
    if from_el is not None:
        raw = "".join(from_el.itertext()).strip()

    if not raw:
        by = el.get("by", "")
        raw = by.lstrip("#").replace("_", " ").strip()

    if not raw:
        return "Unknown", None

    m = re.search(r"\(([^)]+)\)$", raw)
    if m:
        inner = m.group(1).strip()
        name = re.sub(
            r"^(Deputy|Senator|Minister|An |Aire |Teachta |Seanad[ó]ir)\s+",
            "",
            inner,
            flags=re.IGNORECASE,
        ).strip()
        prefix = raw[: m.start()].strip().rstrip(",").strip()
        role = raw if prefix else None
        return name or inner, role

    name = re.sub(
        r"^(Deputy|Senator|An Cathaoirleach|An Ceann Comhairle|An Leas-Cheann Comhairle|An Leas-Chathaoirleach)\s+",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()
    return name or raw, None


def _section_heading(el) -> str | None:
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
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        logger.error("XML parse error for %s %s: %s", chamber, debate_date, e)
        return []

    actual_ns = root.nsmap.get(None) or root.nsmap.get("akn", "")
    if actual_ns and actual_ns != AKN_NS:
        logger.warning("Unexpected AKN namespace %r", actual_ns)
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
                "party": None,
                "role": role,
                "chamber": chamber,
                "debate_title": debate_title,
                "debate_date": debate_date,
                "topic_section": topic,
                "source_url": source_url,
            }
        )

    NS["akn"] = AKN_NS
    return speeches
