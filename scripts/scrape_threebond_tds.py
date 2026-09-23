#!/usr/bin/env python3
"""Resolve and extract source metadata from official ThreeBond TDS PDFs.

The manufacturer's technical-data-sheet index links to /download/ pages that
redirect to canonical PDFs. This script records those PDF URLs, extracts
document metadata and short property evidence snippets, and deliberately does
not store full copyrighted PDF text.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pip._vendor import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
LEADS_PATH = ROOT / "data" / "autonomous-discovered-products.json"
OUTPUT_PATH = ROOT / "data" / "threebond-tds-extractions.json"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
INDEX_LABEL_CORRECTIONS = {
    # The official TDS index labels these links differently from the PDF title.
    "TB1101": "TB1102",
    "TB1772M": "TB1771M",
    "TB2027G": "TB3027G",
    "TB2206": "TB2206S",
}
PROPERTY_TERMS = {
    "appearance": r"appearance",
    "viscosity": r"viscosity",
    "mainComponent": r"main component",
    "tackFreeTime": r"tack.free time",
    "curingSpeed": r"curing speed",
    "lapShear": r"lap shear",
    "tensileStrength": r"tensile strength",
    "hardness": r"hardness",
    "elongation": r"elongation",
    "serviceTemperature": r"service(?:able)? temperature",
}
TITLE_RE = re.compile(
    r"(?im)^\s*(TB\s*[0-9A-Z]+(?:-[0-9A-Z]+)?(?:/\s*(?:TB\s*)?[0-9A-Z]+)?)\s*[–—-]\s*(.+?)\s*$"
)


def compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_document(entry: dict) -> dict:
    url = entry["officialUrl"]
    result = {
        "maker": "ThreeBond",
        "catalogName": entry.get("name"),
        "catalogNameAliases": entry.get("nameAliases", []),
        "sourcePageUrl": url,
        "pdfUrl": None,
        "httpStatus": None,
        "pageCount": None,
        "title": None,
        "productCodeInTds": None,
        "revision": None,
        "issuedDate": None,
        "documentControlNumber": None,
        "textExtractionStatus": "not-processed",
        "propertyEvidence": {},
    }
    try:
        response = requests.get(url, allow_redirects=True, timeout=35, headers=HEADERS)
        result["httpStatus"] = response.status_code
        if response.status_code != 200 or "pdf" not in response.headers.get("content-type", "").lower():
            result["textExtractionStatus"] = "source-unavailable-or-not-pdf"
            return result
        result["pdfUrl"] = response.url
        reader = PdfReader(BytesIO(response.content))
        result["pageCount"] = len(reader.pages)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        flat = compact(text)
        if not flat:
            result["textExtractionStatus"] = "no-text-layer"
            return result
        result["textExtractionStatus"] = "text-extracted"

        title = TITLE_RE.search(text)
        if title:
            result["productCodeInTds"] = re.sub(r"\s+", "", title.group(1)).upper()
            result["title"] = compact(f"{title.group(1)} – {title.group(2)}")
        elif re.search(r"TB\s*3923\s*/\s*TB\s*3928", text, re.I):
            result["productCodeInTds"] = "TB3923/TB3928"
            result["title"] = "TB3923/TB3928 Structural Acrylic Adhesive"
        else:
            result["title"] = next(
                (line.strip() for line in text.splitlines() if "technical data sheet" in line.lower()),
                None,
            )
        for key, pattern in (
            ("revision", r"\bRev\.?\s*:?\s*([\w.\-/]+)"),
            ("issuedDate", r"Issued\s+Date\s*:?\s*([^\n\r]+)"),
            ("documentControlNumber", r"Document\s+Control\s+Number\s*:?\s*([^\n\r]+)"),
        ):
            match = re.search(pattern, text, re.I)
            if match:
                result[key] = compact(match.group(1))[:100]

        lines = [compact(line) for line in text.splitlines() if compact(line)]
        for key, pattern in PROPERTY_TERMS.items():
            for index, line in enumerate(lines):
                if re.search(pattern, line, re.I):
                    evidence = " | ".join(lines[max(0, index - 1):min(len(lines), index + 3)])
                    result["propertyEvidence"][key] = evidence[:280]
                    break

        for old, corrected in INDEX_LABEL_CORRECTIONS.items():
            if (
                (entry.get("name") == old and result["productCodeInTds"] == corrected)
                or (old in entry.get("nameAliases", []) and entry.get("name") == corrected)
            ):
                result["indexLabelCorrection"] = {
                    "from": old,
                    "to": corrected,
                    "basis": "product identifier printed in official TDS PDF",
                }
                break
    except Exception as exc:  # noqa: BLE001
        result["textExtractionStatus"] = f"extraction-error:{type(exc).__name__}"
        result["error"] = str(exc)[:200]
    return result


def main() -> None:
    payload = json.loads(LEADS_PATH.read_text(encoding="utf-8"))
    leads = [entry for entry in payload.get("entries", []) if entry.get("maker") == "ThreeBond"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(extract_document, leads))

    by_source = {result["sourcePageUrl"]: result for result in results}
    removed_unavailable = 0
    linked = 0
    for entry in leads:
        result = by_source[entry["officialUrl"]]
        if not result.get("pdfUrl"):
            entry["tdsDocuments"] = [
                document for document in entry.get("tdsDocuments", [])
                if document.get("url") != result.get("pdfUrl")
            ]
            removed_unavailable += 1
            continue

        old_name = entry.get("name", "")
        corrected_name = INDEX_LABEL_CORRECTIONS.get(old_name)
        pdf_filename = result.get("pdfUrl", "").rsplit("/", 1)[-1].upper()
        normalized_filename = re.sub(r"[^0-9A-Z]", "", pdf_filename)
        normalized_corrected = re.sub(
            r"[^0-9A-Z]", "", (corrected_name or "").removeprefix("TB")
        )
        if corrected_name and (
            result.get("productCodeInTds") == corrected_name
            or normalized_corrected in normalized_filename
        ):
            result["productCodeInTds"] = corrected_name
            if not result.get("indexLabelCorrection"):
                result["indexLabelCorrection"] = {
                    "from": old_name,
                    "to": corrected_name,
                    "basis": "canonical PDF filename and manufacturer TDS index URL",
                }
            entry["nameAliases"] = list(dict.fromkeys([*entry.get("nameAliases", []), old_name]))
            entry["name"] = corrected_name
            entry["sourceLabel"] = "ThreeBond TDS index; displayed name verified against PDF title"

        label_code = entry.get("name", "").upper().replace(" ", "")
        doc_code = (result.get("productCodeInTds") or "").upper().replace(" ", "")
        compound_pair_match = (
            entry.get("name") == "TB3923/28"
            and "3923" in doc_code
            and "3928" in doc_code
        )
        if doc_code and doc_code not in label_code and not compound_pair_match:
            result["associationReview"] = (
                "The PDF's printed product identifier does not match the catalog label; review association."
            )
        document = {
            "url": result["pdfUrl"],
            "label": result.get("title") or f"ThreeBond {entry.get('name')} Technical Data Sheet",
            "productCodeInTds": result.get("productCodeInTds"),
            "catalogNameAliases": entry.get("nameAliases", []),
            "documentType": "TDS",
            "sourcePageUrl": entry["officialUrl"],
            "documentRevision": result.get("revision"),
            "issuedDate": result.get("issuedDate"),
            "documentControlNumber": result.get("documentControlNumber"),
            "pageCount": result.get("pageCount"),
            "textExtractionStatus": result.get("textExtractionStatus"),
            "propertyEvidence": result.get("propertyEvidence", {}),
        }
        if result.get("associationReview"):
            document["associationReview"] = result["associationReview"]
        if result.get("textExtractionStatus") != "source-unavailable-or-not-pdf":
            entry["tdsDocuments"] = [document]
            linked += 1

    total_tds = sum(len(entry.get("tdsDocuments", [])) for entry in payload["entries"])
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
    payload["stats"]["tdsDocumentsLinked"] = total_tds
    payload["stats"]["technicalDocumentsLinked"] = sum(
        len(entry.get("technicalDocuments", [])) for entry in payload["entries"]
    )
    payload["stats"]["tdsDocumentsDiscovered"] = linked
    payload["documentCoverageByManufacturer"] = coverage
    LEADS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": "ThreeBond official technical data sheet index and linked manufacturer PDFs",
        "totalLeads": len(leads),
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "documentsWithText": sum(row["textExtractionStatus"] == "text-extracted" for row in results),
        "documentsWithoutTextLayer": sum(row["textExtractionStatus"] == "no-text-layer" for row in results),
        "indexLabelCorrections": len({
            (row["indexLabelCorrection"]["from"], row["indexLabelCorrection"]["to"])
            for row in results if row.get("indexLabelCorrection")
        }),
        "documents": results,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "threeBondLeads": len(leads),
        "pdfsResolved": sum(bool(row.get("pdfUrl")) for row in results),
        "linked": linked,
        "unavailable": removed_unavailable,
        "textExtracted": sum(row["textExtractionStatus"] == "text-extracted" for row in results),
        "noTextLayer": sum(row["textExtractionStatus"] == "no-text-layer" for row in results),
        "threeBondCoverage": coverage.get("ThreeBond"),
        "allTdsLinked": total_tds,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
