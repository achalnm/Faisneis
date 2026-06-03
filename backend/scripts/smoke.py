"""
Throwaway smoke test. Fetches one real Dail debate and one real CSO table,
prints samples from each so we can confirm the API shapes before building
any pipeline code.

Run from backend/ with:
    python scripts/smoke.py
"""

import json
import sys
import time

import httpx
from lxml import etree

DEBATES_BASE = "https://api.oireachtas.ie/v1"
CSO_BASE = "https://ws.cso.ie/public/api.restful"


def fetch_debate():
    print("\n--- Oireachtas: fetching Dail debate list ---")
    url = f"{DEBATES_BASE}/debates"
    params = {
        "chamber_type": "house",
        "chamber": "dail",
        "date_start": "2024-01-15",
        "date_end": "2024-01-31",
        "limit": 1,
        "skip": 0,
    }
    r = httpx.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    print(f"Got {len(results)} debate record(s)")
    dr = results[0]["debateRecord"]

    house = dr.get("house", {}).get("showAs", "?")
    date = dr.get("date", "?")
    counts = dr.get("counts", {})
    print(f"  House: {house}, Date: {date}, Sections: {counts.get('debateSectionCount')}")

    # XML URI lives at debateRecord["formats"]["xml"]["uri"]
    formats = dr.get("formats", {})
    xml_entry = formats.get("xml")
    xml_uri = xml_entry.get("uri") if isinstance(xml_entry, dict) else None
    print(f"  xml.uri: {xml_uri}")

    if not xml_uri:
        print("  No xml.uri found - cannot continue")
        return

    # The human-readable URL pattern
    # debateRecord URI: https://data.oireachtas.ie/akn/ie/debateRecord/dail/2024-01-31/debate/main
    record_uri = dr.get("uri", "")
    human_url = None
    if "/debateRecord/" in record_uri:
        # extract chamber + date
        parts = record_uri.split("/debateRecord/")[1].split("/")
        if len(parts) >= 2:
            chamber_slug, date_slug = parts[0], parts[1]
            human_url = f"https://www.oireachtas.ie/en/debates/debate/{chamber_slug}/{date_slug}/"
    print(f"  Human URL: {human_url}")

    time.sleep(0.3)
    fetch_and_parse_xml(xml_uri)


def fetch_and_parse_xml(xml_uri: str):
    print(f"\n--- Fetching debate XML ({xml_uri}) ---")
    r = httpx.get(xml_uri, timeout=60, follow_redirects=True)
    r.raise_for_status()
    print(f"  XML size: {len(r.content):,} bytes")

    root = etree.fromstring(r.content)

    # AKN namespace
    ns = {}
    tag = root.tag
    if tag.startswith("{"):
        ns_uri = tag[1: tag.index("}")]
        ns["akn"] = ns_uri
        print(f"  AKN namespace: {ns_uri}")

    speeches = root.findall(".//akn:speech", ns) if ns else root.findall(".//speech")
    questions = root.findall(".//akn:question", ns) if ns else root.findall(".//question")
    answers = root.findall(".//akn:answer", ns) if ns else root.findall(".//answer")
    all_speech_like = speeches + questions + answers
    print(f"  speech/question/answer elements: {len(all_speech_like)}")

    printed = 0
    for sp in all_speech_like:
        if printed >= 3:
            break

        # Speaker from @by attribute or <from> child
        speaker = sp.get("by", "")
        if speaker.startswith("#"):
            speaker = speaker.lstrip("#")
        from_el = sp.find("akn:from", ns) if ns else sp.find("from")
        if from_el is not None and from_el.text:
            speaker = from_el.text.strip()

        paras = sp.findall(".//akn:p", ns) if ns else sp.findall(".//p")
        text = " ".join((p.text or "").strip() for p in paras if p.text)
        if not text.strip():
            continue

        print(f"\n  Speech {printed + 1}:")
        print(f"    Speaker: {speaker or '(unknown)'}")
        print(f"    Text:    {text[:250]}...")
        printed += 1

    # Pull a section title as well
    sections = root.findall(".//akn:debateSection", ns) if ns else root.findall(".//debateSection")
    if sections:
        heading_el = sections[0].find(".//akn:heading", ns) if ns else sections[0].find(".//heading")
        if heading_el is not None:
            print(f"\n  First section heading: {heading_el.text}")


def fetch_cso():
    print("\n\n--- CSO: fetching table catalog ---")
    toc_url = f"{CSO_BASE}/PxStat.Data.Cube_API.ReadCollection"
    r = httpx.get(toc_url, timeout=60)
    r.raise_for_status()
    toc = r.json()

    items = toc.get("link", {}).get("item", [])
    print(f"  Total tables in catalog: {len(items)}")

    # Matrix code lives at item["extension"]["matrix"]
    cpi_matrix = None
    cpi_href = None
    for item in items:
        label = item.get("label", "")
        ext = item.get("extension", {})
        matrix = ext.get("matrix", "")
        if label.lower() == "consumer price index" and "TLIST(M1)" in item.get("id", []):
            print(f"  CPI monthly table found: matrix={matrix!r}, label={label!r}")
            if cpi_matrix is None:
                cpi_matrix = matrix
                cpi_href = item.get("href", "")

    if not cpi_matrix:
        print("  No exact CPI match; falling back to first item with 'consumer price' in title")
        for item in items:
            if "consumer price" in item.get("label", "").lower():
                cpi_matrix = item.get("extension", {}).get("matrix", "")
                cpi_href = item.get("href", "")
                break

    print(f"\n  Using matrix: {cpi_matrix}")
    print(f"  Dataset href: {cpi_href}")
    time.sleep(0.5)

    # Fetch the actual dataset; use the official host regardless of catalog href
    ds_url = f"{CSO_BASE}/PxStat.Data.Cube_API.ReadDataset/{cpi_matrix}/JSON-stat/2.0/en"
    print(f"\n  Fetching dataset from {ds_url}")
    r2 = httpx.get(ds_url, timeout=60)
    r2.raise_for_status()
    ds = r2.json()
    print(f"  Dataset keys: {list(ds.keys())[:8]}")
    print(f"  Label: {ds.get('label')}")

    dims = ds.get("dimension", {})
    print(f"  Dimensions: {list(dims.keys())}")
    for dim_id, dim_data in list(dims.items())[:3]:
        cats = dim_data.get("category", {})
        labels = cats.get("label", {})
        sample = list(labels.items())[:4]
        print(f"    {dim_id} ({dim_data.get('label', '')}): {len(labels)} categories, sample={sample}")

    values = ds.get("value", [])
    print(f"\n  Value array length: {len(values)}")
    print(f"  First 10 values: {values[:10]}")
    print(f"\n  Source URL: https://data.cso.ie/table/{cpi_matrix}")


def main():
    try:
        fetch_debate()
        fetch_cso()
        print("\n\nSmoke test complete.")
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP error: {e.response.status_code} on {e.request.url}")
        print(e.response.text[:1000])
        sys.exit(1)
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
