#!/usr/bin/env python3
"""Fast, dependency-free structural quality gate for .xlsx workbooks."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
ERROR_RE = re.compile(r"#(?:REF!|DIV/0!|VALUE!|NAME\?|N/A|NUM!|NULL!)", re.I)


def qname(namespace: str, tag: str) -> str:
    return f"{{{namespace}}}{tag}"


def parse_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(archive.read(name))


def workbook_report(path: Path) -> dict:
    report = {
        "file": str(path),
        "blocking_errors": [],
        "warnings": [],
        "summary": {},
        "sheets": [],
    }

    if not path.exists():
        report["blocking_errors"].append("Workbook not found")
        return report
    if path.suffix.lower() != ".xlsx":
        report["blocking_errors"].append("Expected an .xlsx workbook")
        return report

    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as exc:
        report["blocking_errors"].append(f"Cannot open workbook package: {exc}")
        return report

    with archive:
        names = set(archive.namelist())
        required = {"xl/workbook.xml", "xl/_rels/workbook.xml.rels"}
        missing = sorted(required - names)
        if missing:
            report["blocking_errors"].append(f"Missing required package parts: {', '.join(missing)}")
            return report

        workbook = parse_xml(archive, "xl/workbook.xml")
        rels = parse_xml(archive, "xl/_rels/workbook.xml.rels")
        rel_targets = {
            rel.attrib["Id"]: rel.attrib.get("Target", "")
            for rel in rels.findall(qname(PKG_REL, "Relationship"))
        }

        calc_pr = workbook.find(qname(MAIN, "calcPr"))
        calc_mode = calc_pr.attrib.get("calcMode", "auto") if calc_pr is not None else "auto"
        if calc_mode == "manual":
            report["blocking_errors"].append("Workbook calculation mode is manual")

        formula_count = 0
        cached_error_count = 0
        conditional_format_count = 0
        merged_area_count = 0
        formula_errors = []
        cached_errors = []
        formula_by_sheet = defaultdict(int)

        sheets_el = workbook.find(qname(MAIN, "sheets"))
        sheet_nodes = list(sheets_el) if sheets_el is not None else []
        for sheet in sheet_nodes:
            sheet_name = sheet.attrib.get("name", "Unnamed")
            state = sheet.attrib.get("state", "visible")
            rel_id = sheet.attrib.get(qname(REL, "id"), "")
            target = rel_targets.get(rel_id, "")
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            target = str(Path(target))

            sheet_info = {
                "name": sheet_name,
                "state": state,
                "formulas": 0,
                "conditional_formats": 0,
                "merged_areas": 0,
                "frozen_panes": False,
            }
            if target not in names:
                report["blocking_errors"].append(f"Worksheet XML missing for {sheet_name}")
                report["sheets"].append(sheet_info)
                continue

            root = parse_xml(archive, target)
            formulas = root.findall(f".//{qname(MAIN, 'f')}")
            sheet_info["formulas"] = len(formulas)
            formula_count += len(formulas)
            formula_by_sheet[sheet_name] += len(formulas)

            for formula in formulas:
                text = formula.text or ""
                if ERROR_RE.search(text):
                    formula_errors.append({"sheet": sheet_name, "formula": text[:180]})

            for cell in root.findall(f".//{qname(MAIN, 'c')}"):
                if cell.attrib.get("t") == "e":
                    value = cell.find(qname(MAIN, "v"))
                    cached_errors.append(
                        {
                            "sheet": sheet_name,
                            "cell": cell.attrib.get("r"),
                            "error": value.text if value is not None else "unknown",
                        }
                    )

            cfs = root.findall(f".//{qname(MAIN, 'conditionalFormatting')}")
            merges = root.findall(f".//{qname(MAIN, 'mergeCell')}")
            panes = root.findall(f".//{qname(MAIN, 'pane')}")
            sheet_info["conditional_formats"] = len(cfs)
            sheet_info["merged_areas"] = len(merges)
            sheet_info["frozen_panes"] = any(
                pane.attrib.get("state") in {"frozen", "frozenSplit"} for pane in panes
            )
            conditional_format_count += len(cfs)
            merged_area_count += len(merges)
            report["sheets"].append(sheet_info)

        cached_error_count = len(cached_errors)
        if formula_errors:
            report["blocking_errors"].append(
                f"{len(formula_errors)} formula(s) contain an error token"
            )
        if cached_errors:
            report["blocking_errors"].append(
                f"{len(cached_errors)} cached cell error(s) found"
            )

        visible_sheets = [s for s in report["sheets"] if s["state"] == "visible"]
        if not visible_sheets:
            report["blocking_errors"].append("Workbook has no visible sheet")

        control_names = [
            s["name"] for s in report["sheets"]
            if re.search(r"contr[oô]le|control|audit|check", s["name"], re.I)
        ]
        if not control_names:
            report["warnings"].append("No sheet name suggests an explicit control/audit layer")

        if formula_count == 0:
            report["warnings"].append("No formulas found; verify that the deliverable is not a static mock-up")

        charts = sorted(
            name for name in names
            if re.fullmatch(r"xl/(?:charts|drawings/charts)/chart\d+\.xml", name)
        )
        drawings = sorted(name for name in names if name.startswith("xl/drawings/drawing") and name.endswith(".xml"))
        external_links = sorted(name for name in names if name.startswith("xl/externalLinks/"))
        if external_links:
            report["warnings"].append(f"Workbook contains {len(external_links)} external-link package part(s)")

        report["details"] = {
            "formula_errors": formula_errors[:50],
            "cached_errors": cached_errors[:50],
            "control_sheets": control_names,
        }
        report["summary"] = {
            "status": "FAIL" if report["blocking_errors"] else "PASS",
            "sheet_count": len(report["sheets"]),
            "visible_sheet_count": len(visible_sheets),
            "formula_count": formula_count,
            "cached_error_count": cached_error_count,
            "chart_count": len(charts),
            "drawing_count": len(drawings),
            "conditional_format_count": conditional_format_count,
            "merged_area_count": merged_area_count,
            "calculation_mode": calc_mode,
            "external_link_part_count": len(external_links),
        }

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    report = workbook_report(args.workbook)
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.json_out:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    return 2 if report["blocking_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
