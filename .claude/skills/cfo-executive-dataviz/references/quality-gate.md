# Quality gate before delivery

The workbook must have no blocking defect and should score at least 90/100.

## Blocking defects

Do not deliver while any of these remain:

- visible `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?` or unexplained `#N/A`;
- group totals do not reconcile to detail;
- a displayed filter does not affect the view and is not marked static;
- a chart is empty, clipped, materially misleading or linked to the wrong range;
- units, scenario or period are ambiguous on a headline KPI;
- a formula-driven result has been replaced by a hardcoded number;
- the source file has been overwritten without authorization;
- sensitive raw data has been exposed on an executive page unnecessarily.

## Scoring rubric

### Financial integrity — 30 points

- 10: material totals reconcile.
- 6: formulas and denominators are correct.
- 5: periods and scenarios are consistent.
- 4: units, signs and precision are coherent.
- 5: assumptions and theoretical values are labeled.

### Decision usefulness — 25 points

- 7: headline KPIs answer the executive question.
- 6: driver visuals explain outcome variance.
- 5: exceptions and value at stake are visible.
- 4: actions follow from quantified facts.
- 3: portfolio or drilldown grain is actionable.

### Visual execution — 25 points

- 6: clear hierarchy and aligned layout.
- 5: restrained, semantic palette.
- 4: typography is readable at normal zoom.
- 4: charts are well chosen and correctly scaled.
- 3: tables have strong scanability.
- 3: spacing, borders and density feel deliberate.

### Engineering and usability — 20 points

- 5: source, calculations, views and controls are traceable.
- 4: filters, freeze panes and navigation work.
- 4: workbook recalculates without errors or broken links.
- 4: user-facing sheets pass rendered visual inspection.
- 3: the file opens cleanly and has a clear final filename.

## Required verification pass

1. Recalculate in a compatible spreadsheet engine.
2. Scan formulas and cached cell errors.
3. Inspect control sheet values and tolerances.
4. Render every user-facing sheet.
5. Check at normal zoom and at fit-to-width.
6. Verify chart titles, axes, legends, labels and ranges.
7. Verify conditional formatting and sparklines on first, middle and last rows.
8. Confirm active filters, source, period and scenario.
9. Confirm no temporary sheets, debugging labels or hidden helper noise are exposed.
10. Save, reopen and repeat the error scan.

For an `.xlsx` generated outside Excel, perform at least one real open–recalculate–save round trip in Excel or LibreOffice when available. A preview renderer can hide malformed shared formulas or unsupported Sparkline extensions.

Use `scripts/quality_gate.py` for a fast structural scan. It complements rather than replaces recalculation and visual inspection.
