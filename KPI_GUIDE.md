# KPI guide by role

Status: **Built** = in the app now on the current Gold tables. **Needs column** = built, switches on when the Gold column listed arrives. **Not possible** = needs data the Gold layer does not hold.
These are standard property & casualty measures chosen for a flood book; they are not the output of a literature search, so have the lead confirm the list and the thresholds (SLA days, credibility years).

## Claims adjuster (page: Claims Desk)
Question: *what do I work on next, and what looks off?*

| KPI | Definition | Status |
|---|---|---|
| Open queue, oldest first | Open claims by days since reported | Needs column: `claim_status`, `date_reported` |
| Aging buckets | 0-30 / 31-60 / 61-90 / 90+ days open | Needs column: same |
| Past SLA | Open longer than N days (N set on the page, default 60) | Needs column: same |
| Time to close | Days from reported to closed: median, 90th percentile, trend | Needs column: `date_closed` |
| My workload | Open claims, avg age, median close time per adjuster | Needs column: `adjuster_name` |
| Waiting-period check | Loss within 30 days of policy start (NFIP policies normally carry a 30-day wait) | Built |
| Repeat loss | More than one claim on the property | Built (exact with `property_id` on policy report) |
| Coverage used | Paid ÷ coverage; flagged above 75% | Built |
| Reporting lag | Days from loss to reported; flagged above 30 | Needs column: `date_reported` |
| Property context | Flood zone, risk band, mitigation, repetitive-loss flag on the claim row | Built (needs `property_id` on policy report) |
| Reserve adequacy, litigation, subrogation / salvage recovery | | Not possible (no reserves, legal or recovery data) |

## Insurance manager (page: Management)
Question: *is the book profitable, is claims handling healthy, and where are we exposed?*

| KPI | Definition | Status |
|---|---|---|
| Paid loss ratio | Claims paid ÷ earned premium; all time, 12 m, by year, cumulative | Built |
| Loss ratio by segment | State, county, flood zone, risk band, construction, agent | Built (exact with `property_id`/`customer_id` on policy report, otherwise estimated) |
| Claim frequency | Claims per 100 policy-years | Built |
| Severity | Average paid per paid claim | Built |
| Pure premium | Claims paid per policy-year | Built |
| Premium per $1k of cover | Active premium ÷ insured value x 1000 | Built |
| Renewal rate | Policy terms followed by another on the same property within 60 days | Needs column: `property_id` on policy report |
| Backlog and time to close | Open claims, aging, median / P90 days to close | Needs column: claim lifecycle |
| Adjuster workload | Open, past-SLA, average age and close time per adjuster | Needs column: `adjuster_name` |
| Risk-weighted exposure | Insured value x risk score ÷ 100, by band | Built |
| Pricing adequacy | Premium share ÷ risk-weighted exposure share, by band (above 1 = premium ahead of risk) | Built |
| Concentration | Top-3 county share and Herfindahl index (HHI) of active insured value | Built |
| Pre-FIRM share, mitigation coverage, repetitive-loss count | Share of insured value built before flood maps; share of high-risk properties with mitigation | Built |
| Incurred loss ratio, combined ratio, expense / LAE ratio | | Not possible (no reserves or expenses) |
| Catastrophe-adjusted loss ratio, PML / AAL | | Not possible (needs a catastrophe model or event tagging on claims) |

## Underwriter / portfolio (page: Loss Ratios, Management > Risk & portfolio)
Loss ratio by risk band and county with credibility weighting, risk vs loss ratio by county, pricing adequacy by band. Quote and bind metrics (hit ratio, quote-to-bind) are not possible: quotes are not in Gold.

## Reading customer-level loss ratios
Customer loss ratios are volatile (one claim on a young policy can show several hundred percent). Use the **adjusted loss ratio** to rank; the raw ratio is shown beside it with the credibility weight. At portfolio level and over multiple years the ratio is stable, and the cumulative line on the yearly chart shows it settling.
