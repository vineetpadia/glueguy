#!/usr/bin/env python3
"""Link verified J-B Weld product data sheets and extract searchable evidence."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pip._vendor import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
LEADS_PATH = ROOT / "data" / "autonomous-discovered-products.json"
OUTPUT_PATH = ROOT / "data" / "jbweld-tds-extractions.json"
SOURCE = {
    "codes": ["8265S", "8281"],
    "url": "https://res.cloudinary.com/iwh/image/upload/q_auto%2Cg_center/assets/1/26/J-B-Weld_803-8281_Cold-Weld-Epoxy_DataSheet_0125.pdf",
}


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def main() -> None:
    response = requests.get(SOURCE["url"], timeout=(20, 90))
    response.raise_for_status()
    if "pdf" not in response.headers.get("content-type", "").lower():
        raise RuntimeError("J-B Weld product data sheet URL did not return a PDF")
    pdf_url = response.url
    reader = PdfReader(BytesIO(response.content))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if not compact(text):
        raise RuntimeError("J-B Weld product data sheet has no extractable text")

    payload = json.loads(LEADS_PATH.read_text(encoding="utf-8"))
    evidence = {
        "chemistry": "Original Cold-Weld two-part epoxy system; 1:1 mix ratio",
        "setTime": "Sets in 4-6 hours",
        "cureTime": "Full cure in 15-24 hours",
        "tensileStrength": "5020 PSI (October 2020 product data sheet; current product page reports 6220 PSI)",
        "serviceTemperature": "Up to 550°F when fully cured",
        "appearance": "Cures to dark grey",
    }
    targets = []
    new_document = False
    for entry in payload["entries"]:
        name = entry.get("name", "")
        if entry.get("maker") != "J-B Weld" or not any(code in name for code in ("Twin Tube", "Professional Size")):
            continue
        if not re.search(r"J-B\s*Weld", name, re.I) or re.search(r"KwikWeld|ClearWeld|MarineWeld", name, re.I):
            continue
        doc = {
            "url": pdf_url,
            "label": "J-B Weld Original Cold-Weld Epoxy Product Data Sheet",
            "documentType": "TDS",
            "documentRevision": "October 2020",
            "pageCount": len(reader.pages),
            "textExtractionStatus": "text-extracted",
            "propertyEvidence": evidence,
        }
        docs = entry.setdefault("tdsDocuments", [])
        if not any(item.get("url") == pdf_url for item in docs):
            docs.append(doc)
            new_document = True
        targets.append({"name": name, "officialProductUrl": entry.get("officialUrl")})

    if not targets:
        raise RuntimeError("No J-B Weld Original package listings matched the verified sheet")

    # Recompute maker coverage and document-link totals from the source catalog.
    coverage: dict[str, dict] = {}
    for entry in payload["entries"]:
        maker = entry.get("maker") or "Unknown"
        row = coverage.setdefault(maker, {
            "productLeads": 0, "productsWithTds": 0, "tdsDocuments": 0, "productsWithSds": 0
        })
        row["productLeads"] += 1
        docs = [item for item in entry.get("tdsDocuments", []) if item.get("url")]
        row["tdsDocuments"] += len(docs)
        row["productsWithTds"] += bool(docs)
        row["productsWithSds"] += any(
            item.get("url") and item.get("documentType", item.get("type", "")).upper() == "SDS"
            for item in entry.get("technicalDocuments", [])
        )
    payload["stats"]["discoveredEntries"] = len(payload["entries"])
    payload["stats"]["tdsDocumentsLinked"] = sum(len(entry.get("tdsDocuments", [])) for entry in payload["entries"])
    if new_document:
        payload["stats"]["tdsDocumentsDiscovered"] += 1
    payload["documentCoverageByManufacturer"] = coverage
    LEADS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "J-B Weld branded product data sheet for Original Cold-Weld epoxy",
        "pdfCount": 1,
        "pdfsResolved": 1,
        "documentsWithText": 1,
        "documents": [{
            "maker": "J-B Weld", "productCodes": SOURCE["codes"], "sourceUrl": SOURCE["url"],
            "pdfUrl": pdf_url, "httpStatus": response.status_code, "pageCount": len(reader.pages),
            "title": "J-B Weld Original Cold-Weld Epoxy Product Data Sheet",
            "revisionDate": "October 2020", "textExtractionStatus": "text-extracted",
            "propertyEvidence": evidence,
            "targets": targets,
        }],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"targets": len(targets), "J-B Weld coverage": coverage.get("J-B Weld"), "allTdsLinks": payload["stats"]["tdsDocumentsLinked"]}))


if __name__ == "__main__":
    main()
