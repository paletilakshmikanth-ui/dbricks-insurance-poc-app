# Insurance Dashboard (Databricks Apps, Streamlit) on a Genie space

Same lavender / navy / violet design as before, rebuilt on the Gold tables from `Synthetic_Data_To_Gold`, read through a **Genie space you attach manually**.
With no space attached the app runs on built-in demo data in the **same columns**, so you can check the UI first.

## What's new in this version
| Page | For | What it shows |
|---|---|---|
| **Loss Ratios** | everyone | Paid loss ratio for the portfolio (all time, 12 m, 3 y, 5 y), by year with a cumulative line, by state / county / flood zone / risk band / construction / agent, and **by customer** with a credibility weight. Frequency, severity, pure premium. Funnel chart showing customer loss ratios settle as history grows. |
| **Claims Desk** | claims adjuster | Open queue (oldest first, per adjuster), aging buckets, past-SLA count, time to close (median, 90th percentile, trend), and a "needs review" list (loss within 30 days of policy start, repeat loss on a property, paid near the policy limit, late reporting). Click a row to open Customer 360. |
| **Management** | insurance manager | *Performance* (loss ratio, frequency, severity, pure premium, premium per $1k cover, renewal rate, by state / agent), *Operations* (backlog, aging, time to close, adjuster workload), *Risk & portfolio* (risk-weighted exposure vs premium by band, risk vs loss ratio by county, concentration / HHI, pre-FIRM share, mitigation coverage). |
| **Portfolio & Geography** | everyone | New **map** of the properties (colour by risk band, flood zone, claim history or policy status; filter to open claims, high risk, etc.) and a county-bubble layer coloured by loss ratio / claims per policy / risk. County table now has loss ratio. |
| **Customer 360 > Claims** | everyone | The customer's loss ratio, credibility, credibility-adjusted ratio and the portfolio ratio. |

KPI definitions, who uses what, and what is not computable yet are in `KPI_GUIDE.md`.

### How the loss ratio is calculated (and why it is stable at portfolio level only)
- **Paid loss ratio = claims paid ÷ earned premium.** Earned premium is written premium x share of each policy term that has elapsed at the as-of date. Reserves are not in Gold, so this is not an incurred loss ratio.
- A single customer has few claims, so its ratio swings between 0% and several hundred percent. **Credibility Z = sqrt(policy-years ÷ full-credibility years)**, capped at 100% (default 10 policy-years, adjustable on the page). **Adjusted loss ratio = Z x own + (1 - Z) x portfolio.** Rank customers by the adjusted figure.
- As data grows, policy-years grow, Z rises towards 100% and the adjusted ratio converges to the customer's own. The "spread" chart on the Loss Ratios page shows this happening.

## Columns to add to Gold (the app works without them and says what is missing)
These are all optional: the app loads either way, and the affected sections show a "Not in the Gold tables" note until the columns arrive. Genie is asked for *all columns*, so nothing in the app needs to change when you add them.

| Table | Add | Switches on |
|---|---|---|
| `gold_property_profile` | `latitude`, `longitude` (already in the `property` table of the data model) | Map |
| `gold_policy_report` | `customer_id`, `property_id` | Exact loss ratio by customer / county / zone / band / agent (without them it is **estimated** as current premium x terms and the page says so); renewal rate; claim-to-customer links on the Claims Desk |
| `gold_claim_report` | `claim_status` (OPEN / CLOSED / DENIED), `date_reported`, `date_closed`, `adjuster_id`, `adjuster_name` | Open queue, aging, time to close, SLA, adjuster workload |

Not in the public NFIP data: claim status, reported/closed dates and adjuster are not in the FEMA claims feed, so for the POC they need to be generated in the synthetic step (as policies and customers are) or come from a real claims system. The demo data shows what the pages look like once they exist.

## Set up
1. In the Genie space, add these tables (they live in `synthetic.gold2` by default): `gold_customer_profile`, `gold_property_profile`, `gold_policy_report`, `gold_claim_report`
   (optional, for the disaster chart: `fact_nfip_claim`, `dim_disaster_declaration`).
2. Create the app (Compute -> Apps -> Custom), upload this folder. Under **Resources** add the Genie space with key `genie-space`
   (or set `GENIE_SPACE_ID` to the id after `/rooms/` in the Genie URL).
3. Give the app's **service principal**: CAN RUN on the Genie space, CAN USE on the space's SQL warehouse, and USE CATALOG / USE SCHEMA / SELECT on the Gold schema.
4. Deploy. First load takes about a minute (four Genie questions); results are cached for an hour and shared by all users. "Refresh data" at the bottom of the sidebar re-asks.
5. If your catalog/schema differ, change `GOLD_CATALOG` / `GOLD_SCHEMA` in `app.yaml`.

## Limits to know before this goes beyond the POC
- **Genie returns at most 5,000 rows per question.** Loss ratios sum every policy term and claim, so once `gold_policy_report` or `gold_claim_report` passes 5,000 rows the totals are silently incomplete (the Loss Ratios page warns). For production read these through a SQL warehouse, or pre-aggregate in Gold (e.g. `gold_loss_ratio_by_customer`, `gold_loss_ratio_by_year`).
- **The map shows exact property coordinates.** `latitude` / `longitude` are tagged `PII_LOCATION` in `Data_Modeling`. The map hover leaves off customer names and street addresses; decide who may open the app (or round coordinates to ZIP centroids) before sharing it widely.
- Loss ratio is paid-only (no reserves), premium is NFIP written premium (the demo adds a fee), and the risk score is a POC index, not a probability.

## How the data is read (and why)
- Genie allows about **5 questions per minute per workspace** and returns **at most 5,000 rows** per result. So the app asks **4 wide questions once**
  (one per Gold table), caches them, and paces requests (max 4 per minute, leaving one for the "Ask Genie" page). Charts are computed in the app, not per-chart Genie calls.
- Each question names the table and its columns and asks for raw rows. On-screen source details were removed on purpose; the error screen and "Run diagnostics" still show the SQL when something fails. If Genie returns a different shape the app
  stops with a clear message (missing columns, text-only answer). If a table has more than 5,000 rows the app warns that the result is truncated.
- **Ask Genie** page: free-form questions with the SQL and result table.

## Which Gold table feeds which step
| Step | Source |
|---|---|
| 1 Customer | gold_customer_profile |
| 2-4 Property, location, exposure & risk | gold_property_profile |
| 5 Quote, 6 Underwriting decision, 8 Endorsements | **not in Gold.** Shown as "not in Gold" with the nearest honest proxy (pricing and risk on file) |
| 7 Policy bind | gold_property_profile + gold_policy_report |
| 9 Claim | gold_claim_report + gold_property_profile (date of loss only, no FNOL / reserve / close dates) |
| 10 Loss history, 11 Mitigation | gold_property_profile |
| 12 Renewal | gold_customer_profile / gold_property_profile (due dates, pending flag) |

## Run locally (demo data)
`pip install -r requirements.txt && streamlit run app.py`

## Troubleshooting: "PERMISSION_DENIED ... No access to 'synthetic.gold2.*'"
Unity Catalog permission, not code. The app runs as its **service principal**; it needs (run as the table owner or an admin; the principal is the app's application id,
shown on Compute -> Apps -> your app -> Authorization, and printed on the app's error screen):
```sql
GRANT USE CATALOG ON CATALOG synthetic TO `<application-id>`;
GRANT USE SCHEMA, SELECT ON SCHEMA synthetic.gold2 TO `<application-id>`;
```
plus CAN RUN on the Genie space and CAN USE on its SQL warehouse. Schema-level SELECT covers every table in the space, including the dim_/fact_ tables.

## Troubleshooting: "Genie request failed ... MessageStatus.FAILED"
The app now prints Genie's own reason (for example `TABLES_MISSING_EXCEPTION`). Then:
1. Open the Genie space in Databricks and paste: `Show all rows and all columns from synthetic.gold2.gold_customer_profile. No filter and no limit.` If that fails there too, the problem is in the space (tables not added, wrong catalog/schema name, warehouse stopped), not the app.
2. If it works in the space UI but not in the app, it is the app's service principal: CAN RUN on the space, CAN USE on the warehouse, USE CATALOG / USE SCHEMA / SELECT on the Gold schema.
3. On the error screen click **Run diagnostics** (one tiny question per table) to see which table fails, or **Use demo data for now** to keep working.
4. If Genie adds a `LIMIT` to the SQL the app warns that the table may be incomplete. Add a space instruction such as "When asked for all rows, do not add a LIMIT."

## Navigation
Sidebar: Dashboard (Overview, Process Flow, Customer 360, Portfolio & Geography, Ask Genie) and Records (Customers, Properties, Policies, Claims, Renewals).
Every Overview tile and card opens its list (Properties tile -> property list, Open claims -> open claims, Renewals -> renewals due in 60 days, ...).
Lists have search, filters, CSV export and "select a row to open that customer's journey". The header search box searches customers, properties, policies and claims at once.
Needs Streamlit 1.35+ (row selection, segmented control with fallback).

## Customer 360
Opening the page shows a customer directory (cards with properties, policies, premium and flags such as "Renews in 40d" or "Open claims"), with quick views, sorting and the header search.
Click a card to open that customer's full 360 view; "← All customers" returns to the directory.
