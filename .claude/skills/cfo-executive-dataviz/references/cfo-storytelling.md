# CFO storytelling and control architecture

## Start with the decision, not the chart

For every requested view, identify:

- the audience and review cadence;
- the decision the audience can take;
- the financial outcome being protected or improved;
- the comparison that makes performance interpretable;
- the granularity at which action is possible.

A good cockpit compresses the path from outcome to action:

```text
Outcome → variance → driver → accountable unit → value at stake → decision → control
```

## KPI contract

Before building, define material KPIs with this structure:

| Field | Requirement |
| --- | --- |
| Name | Business-readable label |
| Formula | Exact numerator and denominator |
| Grain | Group, brand, campus, product, class, channel, etc. |
| Period | Monthly, YTD, full year, cohort or academic intake |
| Scenario | Actual, budget, forecast, target, prior year |
| Unit | €, k€, M€, %, headcount, seats, index |
| Favorability | Whether higher or lower is better |
| Source | Sheet, table, query or system |
| Owner | Function able to act on it |

If a KPI’s denominator or period is uncertain, expose the assumption instead of silently inventing precision.

## Executive narrative

Use three levels:

### 1. What happened?

Headline outcomes: revenue, EBITDA, margin, cash, enrollment, volume or another primary business result.

### 2. Why?

Drivers: price, volume, mix, acquisition efficiency, capacity, staffing, external costs, productivity and structure.

### 3. What should management do?

Quantified priorities with owner, timing or at least a concrete action. Avoid generic commentary such as “monitor closely.”

## Comparators

Label every variance. Prefer a deliberate comparator:

- actual vs budget for accountability;
- actual vs prior year for trajectory;
- forecast vs budget for landing risk;
- entity vs group benchmark for portfolio action;
- scenario vs reference for planning choices.

Do not combine incompatible periods or scenarios in one visual without explicit labeling.

## Value at stake

Translate performance gaps into financial magnitude when reasonable:

```text
EBITDA gap to benchmark = MAX(0, benchmark margin × revenue − EBITDA)
```

Label this as theoretical unless it is supported by an executable plan. Similar opportunity calculations may use free capacity, conversion gaps, price gaps or productivity gaps.

## Portfolio quadrants

Use transparent formula rules. Example with margin and utilization relative to the group:

| Margin | Utilization | Class | Typical action |
| --- | --- | --- | --- |
| At/above benchmark | At/above benchmark | Engine | Protect economics and scale selectively |
| At/above benchmark | Below benchmark | Fill opportunity | Recruit into existing capacity before opening |
| Below benchmark | At/above benchmark | Margin rebuild | Reprice, improve mix and productivity |
| Below benchmark | Below benchmark | Arbitration | Redesign, consolidate, close or execute turnaround |

Use business-specific labels when they are clearer. Show the rule and benchmark on the page.

## Reconciliation layer

Create visible controls for material measures. A control table should contain:

- control description;
- measure A;
- expected measure B;
- variance;
- PASS/FAIL with tolerance.

Typical checks:

- group total equals sum of entities;
- brands equal group;
- bridge endpoint equals reported outcome;
- percentages remain within valid ranges;
- expected number of entities is present;
- current filters return a nonempty population;
- opening plus movements equals closing.

Use tolerances appropriate to the unit. Do not hide failures with formatting or rounding.

## Source and caveat language

Each executive view should state source, period, scenario and data freshness. Distinguish:

- accounting or CRM facts;
- model outputs;
- assumptions;
- theoretical benchmarks;
- management commitments.

This distinction is part of the visual design, not a footnote added as an afterthought.

