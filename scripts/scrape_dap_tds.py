#!/usr/bin/env python3
"""Attach verified official DAP TDS PDFs to product leads and extract metadata."""

from __future__ import annotations

import concurrent.futures
import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from pip._vendor import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
LEADS_PATH = ROOT / "data" / "autonomous-discovered-products.json"
OUTPUT_PATH = ROOT / "data" / "dap-tds-extractions.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# URLs were obtained from the TDS links on the matching dap.com product pages
# or DAP's official technical-data-sheet library. Product identity comes from
# the official product page, not from filename similarity alone.
SOURCES = [
    {
        "name": "Weldwood Multi-Purpose Floor Adhesive",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-multi-purpose-floor-adhesive",
        "url": "https://images.dap.com/WW%20Multi-purpose%20floor_TDS_10.1.18.pdf",
    },
    {
        "name": "Weldwood Floor Tile Adhesive",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-floor-tile-adhesive",
        "url": "https://images.dap.com/WW%20Floor%20Tile%20Adhesive_TDS_10.1.18.pdf",
    },
    {
        "name": "Weldwood FRP Adhesive",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-frp-adhesive",
        "url": "https://images.dap.com/WW%20FRP%20Adhesive_TDS_9.21.20.pdf",
    },
    {
        "name": "Weldwood Gel Formula Contact Cement",
        "productUrl": "https://www.dap.com/products/adhesives/contact-cement/weldwood-gel-formula-contact-cement",
        "url": "https://images.dap.com/WW%20Gel%20Contact%20Cement_TDS_5.8.19.pdf",
    },
    {
        "name": "Weldwood Nonflammable Contact Cement",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-nonflammable-contact-cement",
        "url": "https://images.dap.com/WW%20Nonflam%20Contact%20Cement_TDS_5.8.19.pdf",
    },
    {
        "name": "Weldwood Original Contact Cement",
        "productUrl": "https://www.dap.com/products/adhesives/original-contact-neoprene-adhesive",
        "url": "https://images.dap.com/WW%20Original%20Contact%20Cement_TDS.pdf",
    },
    {
        "name": "Weldwood Original Contact Cement Spray Adhesive",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-original-contact-cement-spray-adhesive",
        "url": "https://images.dap.com/Weldwood%20Original%20Spray%20Adhesive%20TDS%203.25.2024_7079800120.pdf",
    },
    {
        "name": "Weldwood Multi-Purpose Spray Adhesive",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-multi-purpose-spray-adhesive",
        "url": "https://images.dap.com/Weldwood%20Multi-Purpose%20Spray%20Adhesive%20TDS%203.25.2024_7079800124.pdf",
    },
    {
        "name": "Weldwood Original Wood Glue",
        "productUrl": "https://www.dap.com/products/adhesives/weldwood-original-wood-glue",
        "url": "https://images.dap.com/ww-wood-glue-tds-final.pdf",
    },
]

PROPERTY_TERMS = {
    "appearance": r"appearance|color|consistency",
    "chemistry": r"vehicle|adhesive base|product description",
    "viscosity": r"viscosity",
    "workLife": r"open time|working time|work time",
    "setTime": r"set time|dry time|tack.free",
    "cureTime": r"full cure|cure time|maximum holding strength",
    "serviceTemperature": r"service temperature|temperature range|heat resistance",
    "tensileStrength": r"tensile strength|bond strength",
    "solids": r"solids",
    "shelfLife": r"shelf life",
}


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def canonical_url(value: str) -> str:
    parts = urlsplit(value)
    path = quote(unquote(parts.path), safe="/:@!$&'()*+,;=%-._~")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def extract_metadata(source: dict) -> dict:
    row = {
        "maker": "DAP",
        "productName": source["name"],
        "officialProductUrl": source["productUrl"],
        "sourceUrl": source["url"],
        "pdfUrl": None,
        "httpStatus": None,
        "pageCount": None,
        "title": None,
        "revisionDate": None,
        "textExtractionStatus": "not-processed",
        "propertyEvidence": {},
    }
    try:
        response = requests.get(source["url"], allow_redirects=True, timeout=40, headers=HEADERS)
        row["httpStatus"] = response.status_code
        if response.status_code != 200 or "pdf" not in response.headers.get("content-type", "").lower():
            row["textExtractionStatus"] = "source-unavailable-or-not-pdf"
            return row
        row["pdfUrl"] = response.url
        reader = PdfReader(BytesIO(response.content))
        row["pageCount"] = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if not compact(text):
            row["textExtractionStatus"] = "no-text-layer"
            return row
        row["textExtractionStatus"] = "text-extracted"
        lines = [compact(line) for line in text.splitlines() if compact(line)]
        title = next((line for line in lines[:35] if re.search(r"WELDWOOD|DAP", line, re.I) and re.search(r"adhesive|glue|cement", line, re.I)), None)
        row["title"] = title[:200] if title else source["name"]
        date = re.search(r"(?m)\b(0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:19|20)\d{2}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b", text, re.I)
        row["revisionDate"] = date.group(0) if date else None
        for key, pattern in PROPERTY_TERMS.items():
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.I):
                    row["propertyEvidence"][key] = " | ".join(lines[max(0, i - 1):min(len(lines), i + 3)])[:360]
                    break
    except Exception as exc:  # noqa: BLE001
        row["textExtractionStatus"] = f"extraction-error:{type(exc).__name__}"
        row["error"] = str(exc)[:240]
    return row


def main() -> None:
    payload = json.loads(LEADS_PATH.read_text(encoding="utf-8"))
    sources = list(SOURCES)
    source_keys = {(source["name"], canonical_url(source["url"])) for source in sources}
    # Include every TDS discovered by the DAP page crawler, including official
    # Spanish variants, so the extraction archive covers the actual catalog.
    for entry in payload["entries"]:
        if entry.get("maker") != "DAP":
            continue
        for document in entry.get("tdsDocuments", []):
            url = document.get("url", "")
            searchable = f"{document.get('label', '')} {url}"
            if document.get("documentType", "").upper() == "SDS" or not re.search(r"technical data|\btds\b", searchable, re.I):
                continue
            key = (entry["name"], canonical_url(url))
            if key not in source_keys:
                source_keys.add(key)
                sources.append({"name": entry["name"], "productUrl": entry.get("officialUrl"), "url": url})
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(extract_metadata, sources))

    dead_urls = {
        canonical_url(row["sourceUrl"])
        for row in results
        if isinstance(row.get("httpStatus"), int) and 400 <= row["httpStatus"] < 500
    }
    # Remove explicitly dead legacy links after checking them, while keeping
    # their 404 evidence in the extraction report for future audits.
    if dead_urls:
        for entry in payload["entries"]:
            if entry.get("maker") != "DAP":
                continue
            entry["tdsDocuments"] = [
                doc for doc in entry.get("tdsDocuments", [])
                if canonical_url(doc.get("url", "")) not in dead_urls
            ]

    new_urls = set()
    linked = []
    for source, result in zip(sources, results):
        if not result.get("pdfUrl"):
            continue
        matches = [entry for entry in payload["entries"] if entry.get("maker") == "DAP" and entry.get("name") == source["name"]]
        if not matches:
            result["linkStatus"] = "product-lead-not-found"
            continue
        for entry in matches:
            document = {
                "url": result["pdfUrl"],
                "label": result.get("title") or f"{source['name']} Technical Data Sheet",
                "documentType": "TDS",
                "documentRevision": result.get("revisionDate"),
                "pageCount": result.get("pageCount"),
                "textExtractionStatus": result.get("textExtractionStatus"),
                "propertyEvidence": result.get("propertyEvidence", {}),
            }
            documents = entry.setdefault("tdsDocuments", [])
            matching_index = next((i for i, doc in enumerate(documents) if doc.get("url") and canonical_url(doc["url"]) == canonical_url(document["url"])), None)
            if matching_index is None:
                documents.append(document)
                new_urls.add(canonical_url(document["url"]))
            else:
                previous_document = documents[matching_index]
                documents[matching_index] = {**previous_document, **document, "label": previous_document.get("label") or document["label"]}
            linked.append({"name": entry["name"], "officialProductUrl": entry.get("officialUrl"), "tdsUrl": document["url"]})
        result["targets"] = [{"name": row["name"], "officialProductUrl": row["officialProductUrl"]} for row in linked if row["name"] == source["name"]]

    coverage = {}
    for entry in payload["entries"]:
        maker = entry.get("maker") or "Unknown"
        row = coverage.setdefault(maker, {"productLeads": 0, "productsWithTds": 0, "tdsDocuments": 0, "productsWithSds": 0})
        row["productLeads"] += 1
        docs = [doc for doc in entry.get("tdsDocuments", []) if doc.get("url")]
        row["tdsDocuments"] += len(docs)
        row["productsWithTds"] += bool(docs)
        row["productsWithSds"] += any(doc.get("documentType", doc.get("type", "")).upper() == "SDS" for doc in entry.get("technicalDocuments", []))
    payload["stats"]["tdsDocumentsLinked"] = sum(len(entry.get("tdsDocuments", [])) for entry in payload["entries"])
    payload["stats"]["tdsDocumentsDiscovered"] += len(new_urls)
    payload["documentCoverageByManufacturer"] = coverage
    LEADS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "DAP official product-page TDS PDF links, downloaded and text-extracted",
        "pdfCount": len(results),
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "documentsWithText": sum(row["textExtractionStatus"] == "text-extracted" for row in results),
        "documents": results,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "documentsWithText": sum(row["textExtractionStatus"] == "text-extracted" for row in results),
        "linkedProductLeads": len(linked),
        "newUniquePdfLinks": len(new_urls),
        "DAPCoverage": coverage.get("DAP"),
        "allTdsLinks": payload["stats"]["tdsDocumentsLinked"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
