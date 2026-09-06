# Visual system for executive finance workbooks

Use this system as a disciplined starting point. Adapt it to an existing brand when the user supplies one.

## Design principles

1. **Hierarchy before decoration**: title, context, KPIs, drivers, decisions, detail.
2. **High information density with breathing room**: compact tables, generous section separation.
3. **One dominant neutral system**: navy, white, pale gray and one primary blue.
4. **Semantic color is scarce**: green for favorable, amber for attention, red for adverse, blue for neutral/action.
5. **Alignment creates polish**: shared left edges, equal card widths, consistent chart baselines and deliberate gutters.

## Recommended palette

| Role | Hex | Use |
| --- | --- | --- |
| Executive navy | `#17233C` | Title bars, major section headers |
| Primary blue | `#2F7DD1` | Navigation, neutral highlights, main series |
| Slate | `#586A82` | Table headers, secondary labels |
| Ink | `#202733` | Main text and KPI values |
| Canvas | `#F2F5F9` | Page background |
| Soft gray | `#E8EEF5` | Filters, group totals, separators |
| Line gray | `#D6DEE8` | Borders and gridlines |
| Positive | `#16936B` | Favorable status and growth |
| Warning | `#B97800` | Attention and watch status |
| Adverse | `#D64545` | Negative status and critical exceptions |
| Capacity orange | `#F07B32` | Capacity or acquisition emphasis |
| Opportunity violet | `#7C63D8` | Value-at-stake or opportunity metric |

Use pale tints of semantic colors for cell fills. Do not place saturated fills behind dense body text.

## Typography

- Prefer Aptos, Arial, Inter or the organization’s supplied corporate font.
- Workbook title: 20–24 pt, bold, white on navy.
- Section title: 11–13 pt, bold, white on navy or ink on canvas.
- KPI value: 20–28 pt, bold.
- KPI label: 8–10 pt, uppercase or small caps, slate.
- Table body: 8.5–10 pt.
- Footnote: 7.5–9 pt, italic, slate.
- Use no more than three effective text sizes on a single visual band.

## Layout grammar

- Hide gridlines on presentation sheets; keep them on raw-data sheets if useful.
- Reserve a narrow top navigation band for views such as Executive, Portfolio, Data and Controls.
- Put title and subtitle on separate rows.
- Keep filters in a single horizontal strip under the title.
- Use equal-height KPI cards. Align label, value, variance and comparison period consistently.
- Use a pale canvas behind sections; use white chart/card surfaces.
- Separate sections with 8–16 px equivalent whitespace or one empty Excel row.
- Use merged cells only for deliberate titles or wide narrative boxes, never as a substitute for table structure.
- Build a board-ready view that is readable at 90–110% zoom without horizontal scrolling when feasible.

## KPI cards

Each card should contain:

1. short label;
2. large value with explicit unit;
3. variance vs a named comparator;
4. semantic color on the variance only;
5. optional micro-trend or target marker.

Never color a negative variance green merely because the numeric sign is positive. Determine favorability from the KPI’s business meaning.

## Charts

- Remove chart borders, shadows and gradients.
- Prefer white plot areas on white cards.
- Use light gray major gridlines only when they aid reading.
- Start bar axes at zero unless a carefully labeled analytical reason justifies otherwise.
- Use direct labels when they are more readable than legends.
- Limit categorical charts to the categories a human can compare comfortably; rank and group the rest.
- Use one highlight series and mute context series.
- Show units in the title or axis, never leave scale ambiguous.
- Keep legends close to the plot and in a consistent position.

For portfolio scatters, use a benchmark point or benchmark lines, meaningful axis ranges and a decision interpretation. A cloud of unlabeled points is not an executive insight.

## Tables and heatmaps

- Use dark slate headers with white text.
- Emphasize group totals and hierarchy parents with pale blue-gray fills and bold text.
- Apply alternating rows only when it improves scanning.
- Right-align measures, left-align labels and center short statuses.
- Use number formats instead of adding units to every cell.
- Use data bars for magnitude, color scales for relative performance and text status fills for decisions.
- Keep conditional formatting semantically stable across all views.
- Add sparklines near the related metric only when the target spreadsheet engine has been round-trip tested. For cross-engine delivery, prefer compact formula-driven trajectories such as `3.6 › 3.9 › 4.3`, with the periods and unit named in the header.

## Common quality failures

- the same accent color everywhere;
- cards with inconsistent width or baseline;
- too many boxed regions and heavy borders;
- tiny labels caused by too many categories;
- a dashboard that reads like a database extract;
- false precision, mixed units or unexplained acronyms;
- large blank zones caused by unplanned print ranges;
- labels clipped at the edge of charts;
- inconsistent favorable/adverse coloring.
