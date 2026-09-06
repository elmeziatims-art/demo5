---
name: cfo-executive-dataviz
description: Create or radically improve board-ready Excel dashboards, CFO cockpits and management-control reporting with refined dataviz, formula-driven metrics, financial reconciliations and visual QA. Use for executive finance dashboards, EPM/FP&A reporting, portfolio views and private-education performance cockpits. Do not use for a simple isolated formula correction or raw data cleaning when no reporting or visualization layer is requested.
---

# CFO Executive Dataviz

Produce a working financial decision tool that is as rigorous as it is visually refined. The target is a workbook a CFO can use in an executive review, not a decorative mock-up.

## Load the relevant guidance

- Read [references/visual-system.md](references/visual-system.md) whenever creating or redesigning a visual layer.
- Read [references/cfo-storytelling.md](references/cfo-storytelling.md) when choosing KPIs, charts, benchmarks, decisions or controls.
- Read [references/private-education.md](references/private-education.md) only for schools, higher education, training groups or similar enrollment-driven businesses.
- Read [references/quality-gate.md](references/quality-gate.md) before final delivery.
- Inspect [assets/reference-cockpit.xlsx](assets/reference-cockpit.xlsx) and [assets/reference-matrice-campus.png](assets/reference-matrice-campus.png) when a concrete quality bar is useful. Treat them as design references, never as a source of business values.

## Choose the operating mode

### Improve an existing workbook

Audit before editing:

1. Inventory sheets, tables, named ranges, formulas, charts, filters, merged areas and hidden content.
2. Identify the source-of-truth cells and reconciliation points.
3. Preserve working logic, user inputs and unrelated formatting.
4. Repair structure only where it improves reliability, readability or decision use.

Never overwrite the source file unless explicitly requested. Produce a clearly named improved copy and keep formulas live.

### Create a new workbook

Build the financial spine before the visual layer:

1. Define grain, dimensions, periods, scenarios and KPI contracts.
2. Separate inputs/source data, calculations, executive views and controls.
3. Reconcile totals before adding charts.
4. Build the dashboard from formula-backed ranges or structured tables.

## Required information architecture

Adapt the number of sheets to the task, but preserve these functions:

- **Data or Inputs**: normalized source data, assumptions and provenance.
- **Calculations**: reusable measures and intermediate logic when needed.
- **Executive view**: one-page hierarchy from group outcome to decisions.
- **Analysis view**: portfolio, entity, campus, product or business-unit drilldown.
- **Controls**: visible audit checks with expected value, variance and PASS/FAIL.

An executive page should normally read in this order:

1. context and active filters;
2. five to seven headline KPIs with prior-year or budget variance;
3. two to four charts explaining trajectory and drivers;
4. explicit management priorities tied to quantified facts;
5. compact portfolio table with exceptions highlighted;
6. source, date, scope and methodological caveats.

## Build for decisions

Each important visual must answer a management question. Use the smallest visual that answers it well.

| Management question | Preferred visual |
| --- | --- |
| How did EBITDA move? | Waterfall or bridge |
| Which entities outperform? | Sorted bars or heatmap table |
| Is growth efficient? | Indexed line, scatter or unit-economics table |
| Where is capacity underused? | Ranked capacity bars |
| Which units need action? | Benchmark scatter with decision quadrants |
| What is the recent trajectory? | Sparkline beside the KPI or entity |
| How is a total composed? | Stacked bar only when components are comparable |

Avoid 3D charts, speedometers, decorative gauges, exploded pies, rainbow palettes and charts that merely repeat a visible table.

Add a decision layer when the data supports it:

- benchmark against group, budget, prior year or target;
- quantify value at stake;
- classify units using transparent formula-driven rules;
- associate each class with a practical management action;
- label theoretical opportunities as such, not as budgets or commitments.

## Engineering invariants

- Derived business numbers must be formulas, queries, pivots or code-generated calculations—not typed results.
- Assumptions may be hardcoded only in clearly identified input cells.
- Use consistent signs, units and denominators. Distinguish euros, thousands and millions explicitly.
- Use weighted rates when aggregation requires them. Never average percentages blindly.
- Keep filters functional; do not show an inert selector as if it were interactive.
- Preserve traceability from executive KPI to detailed source.
- Include reconciliation controls for financially material totals.
- Avoid formula errors, broken external links and manual calculation mode.
- Use locale-compatible number formats and human-readable labels.
- Freeze useful panes, size columns intentionally and keep print/export behavior coherent.

## Visual QA loop

Do not consider the workbook finished after code execution.

1. Recalculate with Excel or LibreOffice when available.
2. Render or export every user-facing sheet.
3. Inspect at normal zoom for clipping, overlap, empty chart series, illegible labels, excessive whitespace, weak contrast and misleading scales.
4. Inspect formulas and cached values for errors.
5. Run `python scripts/quality_gate.py <workbook.xlsx>` when Python is available.
6. Iterate until the workbook clears [references/quality-gate.md](references/quality-gate.md).

If rendering is unavailable, say so and compensate with stronger structural inspection; do not claim pixel-perfect QA.

## Delivery contract

Deliver the final working workbook and summarize:

- what was added or materially improved;
- the most decision-useful insights exposed by the design;
- whether reconciliations and formula-error checks passed;
- any remaining data freshness, scope or methodology caveat.

Keep the handoff concise. The artifact should demonstrate the quality.

