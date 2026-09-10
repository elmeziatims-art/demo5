# Private education and school-group reporting

Use this reference for private higher education, training groups and multi-campus school networks.

## Typical analytical hierarchy

```text
Group → Brand → Campus → Programme → Year of study → Modality → Cohort
```

Preserve the finest actionable grain available, but keep the executive page at group, brand and campus level.

## Core KPI families

### Financial outcome

- Revenue and revenue per student
- EBITDA and EBITDA margin
- Contribution margin by campus, programme or class
- Payroll, teaching cost, occupancy cost, marketing cost and central allocations
- Break-even students per class

### Enrollment and funnel

- Leads, candidates, admitted students, new enrollments and re-enrollments
- Lead-to-candidate, candidate-to-admitted and admitted-to-enrolled conversion
- Re-enrollment or progression rate
- Organic vs paid leads
- Cost per lead, cost per candidate and CAC per new enrollment

### Capacity and delivery

- Headcount, number of classes, class size and theoretical capacity
- Fill rate
- Free seats
- Teaching FTE or hours per student/class
- Campus and programme mix
- Apprenticeship/work-study mix

## Formula discipline

Use weighted aggregation:

```text
Group fill rate = total enrolled students / total theoretical capacity
Group CAC = total acquisition spend / total new enrolled students
Group conversion = total downstream population / total upstream population
Revenue per student = eligible revenue / average or period-appropriate student population
```

Do not average campus rates unless the business question explicitly requires an unweighted entity average.

Estimated free seats may be derived as:

```text
Theoretical capacity = enrolled students / fill rate
Free seats = theoretical capacity − enrolled students
```

Label this estimate and reconcile it later with actual classes and room/class caps.

## Executive questions the dashboard should answer

- Is growth creating EBITDA or consuming margin?
- Which brands and campuses generate the group’s profit?
- Where can growth be absorbed without opening new classes?
- Which full campuses have a margin problem rather than a recruitment problem?
- Where does acquisition spend grow faster than enrollments?
- Which programmes or classes are below break-even?
- What is the impact of closing, merging or not opening a class?
- Is work-study mix supporting revenue and cash economics?
- Which assumptions drive the next budget or forecast?

## Useful decision views

- EBITDA bridge: prior year → activity → price/mix → costs → current year.
- Margin by brand over three periods or scenarios.
- Acquisition spending vs new enrollments as indexed trajectories.
- Campus scatter: fill rate vs EBITDA margin, sized by revenue or students.
- Ranked free-capacity bars by campus.
- Campus heatmap: revenue, EBITDA, margin, fill, free seats, mix, change and value at stake.
- Budget sensitivity table: acquisition, conversion, retention, price, class openings, staffing and external inflation.

## Budget driver tree

For planning, separate human assumptions from automatic calculation:

```text
Acquisition spend → leads → candidates → admitted → new enrollments
Re-enrollment and progression → returning students
New + returning students → classes and capacity
Students × price/mix → revenue
Classes × staffing/teaching rules → delivery costs
Campus + brand + group cost drivers → EBITDA
```

Allow local owners to adjust explicit drivers while automatically recalculating the detailed model. Preserve a reference, target and constructed scenario so adjustments remain explainable.

## Pitfalls

- mixing academic intakes with calendar-year finance without a bridge;
- treating applications, admissions and enrollments as interchangeable;
- comparing CAC without a consistent attribution window;
- ignoring cancellations, deferred starts or incomplete cohorts;
- calculating fill from room capacity when the constraint is class economics;
- allocating central cost in a way that obscures campus operating performance;
- presenting theoretical EBITDA recovery as a committed saving.

