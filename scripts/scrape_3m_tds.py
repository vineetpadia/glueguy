#!/usr/bin/env python3
"""Link verified 3M adhesive TDS PDFs and extract searchable evidence."""

from __future__ import annotations

import concurrent.futures
import json
import re
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pip._vendor import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
LEADS_PATH = ROOT / "data" / "autonomous-discovered-products.json"
OUTPUT_PATH = ROOT / "data" / "3m-tds-extractions.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# URLs were discovered through 3M product resources or its official TDS search
# and independently checked to return application/pdf on multimedia.3m.com.
SOURCES = [
    {
        "codes": ["1386"],
        "url": "https://multimedia.3m.com/mws/media/2366025O/3m-scotch-weld-epoxy-adhesive-1386.pdf?fn=3M-Scotch-Weld-Epoxy-Adhesive-1386.pdf",
    },
    {
        "codes": ["1751"],
        "url": "https://multimedia.3m.com/mws/media/66780O/3m-scotch-weld-epoxy-adhesive-1751-b-a.pdf?fn=TDS_1751-B-A_R1.pdf",
    },
    {
        "codes": ["1838", "1838L"],
        "url": "https://multimedia.3m.com/mws/media/66759O/3m-scotch-weld-epoxy-adhesive-1838-b-a.pdf?fn=78690009648_R3.pdf",
    },
    {
        "codes": ["DP605NS"],
        "url": "https://multimedia.3m.com/mws/media/982016O/3m-scotch-weld-urethane-adhesive-dp605ns.pdf",
    },
    {
        "codes": ["DP810"],
        "url": "https://multimedia.3m.com/mws/media/1235384O/dp810-technical-data-sheets.pdf",
    },
    {
        "codes": ["EC2615"],
        "url": "https://multimedia.3m.com/mws/media/241247O/ec-2615-2615-lw-data-page-qxd.pdf?fn=EC-2615BA.pdf",
    },
    {
        "codes": ["EC2792"],
        "url": "https://multimedia.3m.com/mws/media/807611O/3m-tm-scotch-weld-tm-epoxy-adhesive-ec-2792-b-a-datasheet.pdf",
    },
    {
        "codes": ["EC3542"],
        "url": "https://multimedia.3m.com/mws/media/1422579O/3m-scotch-weld-epoxy-adhesive-ec-3542-ba-fr.pdf?fn=TDS-3M-Scotch-Weld-Epoxy-Adhesive-EC-3542-BA-FR.pdf",
    },
    {
        "codes": ["2214 Hi-Temp"],
        "url": "https://multimedia.3m.com/mws/media/2365952O/3m-scotch-weld-epoxy-adhesive-2214-hi-temp.pdf",
    },
    {
        "codes": ["2214 Non-Metallic Filled"],
        "url": "https://multimedia.3m.com/mws/media/2365997O/3m-scotch-weld-epoxy-adhesive-2214-non-metallic-filled.pdf?fn=3M-Scotch-Weld-Epoxy-Adhesive-2214-Non-Metallic-Filled.pdf",
    },
    {
        "codes": ["2158"],
        "url": "https://multimedia.3m.com/mws/media/2365973O/3m-scotch-weld-epoxy-adhesive-2158-b-a.pdf",
    },
    {
        "codes": ["DP8005"],
        "url": "https://multimedia.3m.com/mws/media/2365892O/3m-scotch-weld-structural-plastic-adhesive-dp8005-black.pdf",
    },
    {
        "codes": ["DP620NS"],
        "url": "https://multimedia.3m.com/mws/media/2365891O/3m-scotch-weld-urethane-adhesive-dp620ns-black.pdf",
    },
    {
        "codes": ["DP8725NS"],
        "url": "https://multimedia.3m.com/mws/media/2365901O/3m-scotch-weld-low-odor-acrylic-adhesive-dp8725ns.pdf",
    },
    {
        "codes": ["DP8825NS"],
        "url": "https://multimedia.3m.com/mws/media/2522980O/3m-scotch-weld-low-odor-acrylic-adhesive-dp8825ns-green.pdf?fn=3M-Scotch-Weld-Low-Odor-Acrylic-Adhesive-DP8825NS-Green.pdf",
    },
]

PROPERTY_TERMS = {
    "appearance": r"appearance|color",
    "chemistry": r"chemistry|base resin|product description",
    "viscosity": r"viscosity",
    "workLife": r"work.?life|work time",
    "setTime": r"set time|handling strength",
    "cureTime": r"full cure|cure time|time to structural strength",
    "lapShear": r"overlap shear|tensile shear|lap shear",
    "serviceTemperature": r"service temperature|temperature resistance",
    "tensileStrength": r"tensile strength",
    "hardness": r"hardness",
}


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_metadata(source: dict) -> dict:
    result = {
        "maker": "3M",
        "productCodes": source["codes"],
        "sourceUrl": source["url"],
        "pdfUrl": None,
        "httpStatus": None,
        "pageCount": None,
        "title": None,
        "revisionDate": None,
        "textExtractionStatus": "not-processed",
        "propertyEvidence": {},
        "targets": [],
    }
    try:
        response = None
        for attempt in range(3):
            try:
                response = requests.get(
                    source["url"], allow_redirects=True, timeout=(20, 90), headers=HEADERS
                )
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        result["httpStatus"] = response.status_code
        if response.status_code != 200 or "pdf" not in response.headers.get("content-type", "").lower():
            result["textExtractionStatus"] = "source-unavailable-or-not-pdf"
            return result
        result["pdfUrl"] = response.url
        reader = PdfReader(BytesIO(response.content))
        result["pageCount"] = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not compact(text):
            result["textExtractionStatus"] = "no-text-layer"
            return result
        result["textExtractionStatus"] = "text-extracted"

        metadata_title = getattr(reader.metadata, "title", None) if reader.metadata else None
        title_match = re.search(
            r"(?im)^\s*(3M.{0,120}(?:" + "|".join(re.escape(c) for c in source["codes"]) + r").{0,100})\s*$",
            text,
        )
        result["title"] = compact(title_match.group(1))[:200] if title_match else compact(metadata_title or "")[:200] or None
        date_pattern = re.compile(
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b.{0,15}\b20\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]20\d{2}\b",
            re.I,
        )
        for line in text.splitlines()[:50]:
            explicit = re.search(
                r"(?:Last\s+Revision\s+Date|Revision\s+Date|Issued\s+Date|Issue\s+Date)\s*:?\s*([^\n\r]+)",
                line,
                re.I,
            )
            candidate = compact(explicit.group(1)) if explicit else ""
            if not candidate and re.search(r"Technical\s+Datasheet|Technical\s+Data\s+Sheet", line, re.I):
                candidate = compact(line)
            date = date_pattern.search(candidate)
            if date:
                result["revisionDate"] = date.group(0)
                break

        lines = [compact(line) for line in text.splitlines() if compact(line)]
        for key, pattern in PROPERTY_TERMS.items():
            for index, line in enumerate(lines):
                if re.search(pattern, line, re.I):
                    result["propertyEvidence"][key] = " | ".join(
                        lines[max(0, index - 1):min(len(lines), index + 3)]
                    )[:320]
                    break
    except Exception as exc:  # noqa: BLE001
        result["textExtractionStatus"] = f"extraction-error:{type(exc).__name__}"
        result["error"] = str(exc)[:200]
    return result


def product_matches(code: str, name: str) -> bool:
    normalized = re.sub(r"[^A-Z0-9]", "", name.upper())
    code_norm = re.sub(r"[^A-Z0-9]", "", code.upper())
    if code_norm == "1838":
        return bool(re.search(r"(?<![A-Z0-9])1838(?!L)(?![A-Z0-9])", name.upper()))
    if code_norm == "DP810":
        return bool(re.search(r"\bDP810\b", name.upper()))
    return code_norm in normalized


def main() -> None:
    payload = json.loads(LEADS_PATH.read_text(encoding="utf-8"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(extract_metadata, SOURCES))

    linked_codes = 0
    new_tds_urls = set()
    for result in results:
        source = next(item for item in SOURCES if item["url"] == result["sourceUrl"])
        if not result.get("pdfUrl"):
            continue
        targets = []
        for code in source["codes"]:
            matched = [
                entry for entry in payload["entries"]
                if entry.get("maker") == "3M" and product_matches(code, entry.get("name", ""))
            ]
            for entry in matched:
                document = {
                    "url": result["pdfUrl"],
                    "label": result.get("title") or f"3M {code} Technical Data Sheet",
                    "documentType": "TDS",
                    "documentRevision": result.get("revisionDate"),
                    "pageCount": result.get("pageCount"),
                    "textExtractionStatus": result.get("textExtractionStatus"),
                    "propertyEvidence": result.get("propertyEvidence", {}),
                }
                documents = entry.setdefault("tdsDocuments", [])
                if not any(doc.get("url") == document["url"] for doc in documents):
                    documents.append(document)
                    new_tds_urls.add(document["url"])
                targets.append({"code": code, "name": entry.get("name"), "officialProductUrl": entry.get("officialUrl")})
                linked_codes += 1
        result["targets"] = targets

    coverage: dict[str, dict] = {}
    for entry in payload["entries"]:
        maker = entry.get("maker") or "Unknown"
        row = coverage.setdefault(maker, {
            "productLeads": 0, "productsWithTds": 0, "tdsDocuments": 0, "productsWithSds": 0
        })
        row["productLeads"] += 1
        docs = [doc for doc in entry.get("tdsDocuments", []) if doc.get("url")]
        row["tdsDocuments"] += len(docs)
        row["productsWithTds"] += bool(docs)
        row["productsWithSds"] += any(
            doc.get("url") and doc.get("documentType", doc.get("type", "")).upper() == "SDS"
            for doc in entry.get("technicalDocuments", [])
        )
    payload["stats"]["discoveredEntries"] = len(payload["entries"])
    payload["stats"]["tdsDocumentsLinked"] = sum(
        len(entry.get("tdsDocuments", [])) for entry in payload["entries"]
    )
    payload["stats"]["tdsDocumentsDiscovered"] += len(new_tds_urls)
    payload["documentCoverageByManufacturer"] = coverage
    LEADS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "3M official multimedia TDS PDFs linked from 3M product resources and TDS search",
        "pdfCount": len(results),
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "documentsWithText": sum(row["textExtractionStatus"] == "text-extracted" for row in results),
        "documents": results,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "linkedProductLeads": linked_codes,
        "newUniquePdfLinks": len(new_tds_urls),
        "3MCoverage": coverage.get("3M"),
        "allTdsLinks": payload["stats"]["tdsDocumentsLinked"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
