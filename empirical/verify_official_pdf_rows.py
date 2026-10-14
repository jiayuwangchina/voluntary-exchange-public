#!/usr/bin/env python3
"""Independently compare the 391 application rows with official report tables.

Requires Python 3; Poppler's pdftotext is required when PDFs are available.
Download the October and December reports from the URLs in SOURCES and place
them in --source-dir under their official names or the short names below.
PDFs are converted in memory with `pdftotext -layout`; no files are downloaded.
Previously extracted October_2025.txt / December_2025.txt are accepted if the
corresponding PDFs are absent. The output identifies which input was used.

Example from the empirical directory:
  python verify_official_pdf_rows.py --source-dir ../source_audit \
      --data ../data/water_randomized_applications_391.csv

This audit verifies the requested quantitative fields and October identifiers.
It does not claim to validate unobserved seller balances or private valuations.
"""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path


BASE = "https://waterregister.vic.gov.au/images/documents/"
SOURCES = {
    "2025-10-15": {
        "short_name": "October_2025",
        "official_name": "Goulburn-to-Murray-Post-Trade-Opening-Report-October-2025.pdf",
        "expected_rows": 203,
    },
    "2025-12-15": {
        "short_name": "December_2025",
        "official_name": "Goulburn-to-Murray-Post-Trade-Opening-Report-December-2025.pdf",
        "expected_rows": 188,
    },
}
NUM = r"[\d,]+(?:\.\d+)?"
# The first four numbers at the right edge of each application row are price,
# volume, opportunity before, and opportunity after. Wrapped reason/type text
# is immaterial to these independently extracted quantitative fields.
PATTERNS = {
    "2025-10-15": re.compile(
        rf"^\s*(\d+)\s+(GTM\d+)\s+(Approved|Refused)(?:\((\d+)\))?"
        rf"\s+.*?\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})(?:\s*\(\d+\))?\s*$"
    ),
    "2025-12-15": re.compile(
        rf"^\s*(\d+)\s+(Approved|Refused)(?:\((\d+)\))?"
        rf"\s+.*?\s+({NUM})\s+({NUM})\s+({NUM})\s+({NUM})(?:\s*\(\d+\))?\s*$"
    ),
}


def number(value):
    return Decimal(value.replace(",", ""))


def get_text(folder, spec):
    for name in [spec["short_name"] + ".pdf", spec["official_name"]]:
        path = folder / name
        if path.exists():
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                check=True, capture_output=True,
            )
            return result.stdout.decode("utf-8"), {
                "input_name": name,
                "input_type": "official_pdf",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "extraction": "pdftotext -layout",
            }
    path = folder / (spec["short_name"] + ".txt")
    if not path.exists():
        raise FileNotFoundError(
            "Download " + BASE + spec["official_name"] + " into " + str(folder)
        )
    return path.read_text(encoding="utf-8"), {
        "input_name": path.name,
        "input_type": "previously_extracted_layout_text",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "extraction": "existing text; PDF provenance requires separate verification",
    }


def extract_rows(text, date):
    rows = {}
    for page_number, page in enumerate(text.split("\f"), 1):
        for line in page.splitlines():
            match = PATTERNS[date].match(line)
            if not match:
                continue
            if date == "2025-10-15":
                priority, identifier, status, footnote, price, volume, before, after = match.groups()
            else:
                priority, status, footnote, price, volume, before, after = match.groups()
                identifier = ""
            priority = int(priority)
            if priority in rows:
                raise AssertionError(f"Duplicate official priority {date}/{priority}")
            rows[priority] = {
                "status": status,
                "status_footnote": footnote or "",
                "price_AUD_per_ML": number(price),
                "volume_ML": number(volume),
                "opportunity_before_ML": number(before),
                "opportunity_after_ML": number(after),
                "source_row_id": identifier,
                "source_physical_page": page_number,
            }
    expected = SOURCES[date]["expected_rows"]
    if set(rows) != set(range(1, expected + 1)):
        raise AssertionError(f"Incomplete official table: {date}, parsed {len(rows)}")
    return rows


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=here.parent / "source_audit")
    parser.add_argument("--data", type=Path, default=here.parent / "data" / "water_randomized_applications_391.csv")
    parser.add_argument("--output", type=Path, default=here / "official_pdf_row_verification.json")
    args = parser.parse_args()
    with args.data.open(newline="", encoding="utf-8-sig") as handle:
        csv_rows = list(csv.DictReader(handle))
    indexed = {}
    for row in csv_rows:
        key = (row["event_date"], int(row["random_priority"]))
        if key in indexed:
            raise AssertionError(f"Duplicate CSV key {key}")
        indexed[key] = row
    expected_keys = {(date, n) for date, spec in SOURCES.items()
                     for n in range(1, spec["expected_rows"] + 1)}
    if set(indexed) != expected_keys:
        raise AssertionError("CSV does not contain exactly the two complete eligible batches")

    report = {
        "passed": True,
        "csv_name": args.data.name,
        "csv_sha256": hashlib.sha256(args.data.read_bytes()).hexdigest(),
        "rows_compared": len(indexed),
        "numeric_method": "Decimal: exact equality, no tolerance or rounding",
        "events": {},
        "mismatches": [],
    }
    fields = ["price_AUD_per_ML", "volume_ML", "opportunity_before_ML", "opportunity_after_ML"]
    for date, spec in SOURCES.items():
        text, provenance = get_text(args.source_dir, spec)
        official = extract_rows(text, date)
        comparisons = 0
        for priority, row in official.items():
            csv_row = indexed[(date, priority)]
            for field in fields + ["status", "source_physical_page", "status_footnote"]:
                expected = row[field]
                value = csv_row[field]
                if field in fields:
                    value = number(value)
                elif field == "source_physical_page":
                    value = int(value)
                elif field == "status_footnote" and value:
                    value = str(int(number(value)))
                comparisons += 1
                if value != expected:
                    report["mismatches"].append({
                        "event_date": date, "priority": priority, "field": field,
                        "official": str(expected), "csv": str(value),
                    })
            if date == "2025-10-15":
                for field, expected in [
                    ("source_row_id", row["source_row_id"]),
                    ("arrival_order", Decimal(int(row["source_row_id"][3:]))),
                ]:
                    value = csv_row[field] if field == "source_row_id" else number(csv_row[field])
                    comparisons += 1
                    if value != expected:
                        report["mismatches"].append({
                            "event_date": date, "priority": priority, "field": field,
                            "official": str(expected), "csv": str(value),
                        })
        report["events"][date] = {
            "source_url": BASE + spec["official_name"],
            **provenance,
            "rows_extracted": len(official),
            "priorities_complete": True,
            "field_comparisons": comparisons,
            "total_volume_ML": str(sum(row["volume_ML"] for row in official.values())),
            "successful_applications": sum(row["status"] == "Approved" for row in official.values()),
            "successful_volume_ML": str(sum(row["volume_ML"] for row in official.values() if row["status"] == "Approved")),
        }
    report["passed"] = not report["mismatches"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "rows_compared": report["rows_compared"],
                      "mismatches": len(report["mismatches"]), "output": str(args.output)}, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
