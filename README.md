# Can you trust a year of NYC public-housing electricity bills?

**NYCHA Electricity 2024: Utility Data Onboarding & Reconciliation**

A self-directed work sample on public data. I treated the NYC Housing Authority (NYCHA) as a mock customer sending its 2024 electricity bills for Scope 2 reporting, and took the raw export to a clean, reconciled activity dataset in Excel Power Query, with every change documented.

| | |
|---|---|
| **Clean 2024 total** | 1,119,058,278 kWh and $185,971,268 across 379 sites (2,366 meters) |
| **Reconciliation** | Raw to clean ties to the kWh and the dollar; every check cell reads 0 |
| **Biggest issue** | 14.6% of kWh comes from estimated meter reads; 149 meters were estimated on every 2024 bill |
| **Built with** | Excel Power Query (Group By, Merge, custom columns, parameter), COUNTIFS / SUMIFS |

**Start here:** [customer memo (PDF)](docs/NYCHA_CY2024_customer_memo.pdf) · **Workbook:** [download from Releases](../../releases/latest) · **Power Query code:** [`queries/`](queries/) · **Source data:** [NYC Open Data jr24-e7cr](https://catalog.data.gov/dataset/electric-consumption-and-cost-2010-may-2025)

---

## The question

A large customer sends a raw utility export. Before anyone reports emissions from it: **are the totals right, and where are the traps?**

## The data

- NYCHA Electric Consumption And Cost (2010 - Sep 2025), NYC Open Data id `jr24-e7cr`, last updated Feb 9, 2026.
- Pull: bills with service ending on or after 2023-12-01 and starting before 2025-02-01, so bills that straddle Jan 1 and Dec 31 are caught. **51,854 rows.**
- Tie-out to the source: 1,374,104,258.56 kWh and $226,136,812.49 across all rows.

## How it works

```
Load & type  ->  Find the grain  ->  Flag issues  ->  Clean  ->  Calendarize  ->  Reconcile
```

1. **Load and type.** IDs stay text (180 rows carry meter IDs with letters, e.g. `9863107_S011600-87.8%`); amounts are numbers; dates are dates. The CSV must be read with quote handling: 634 rows have commas inside quoted names and would otherwise shift columns silently.
2. **Find the grain.** Grouping proves **one row = one bill x one meter**: bill + meter never repeats, while one bill covers up to 68 meters (15,873 bills in total).
3. **Flag issues.** One TRUE/FALSE column per rule, so every issue can be counted, sized and filtered.
4. **Clean.** Each issue gets a documented treatment (kept, merged, filled or excluded) and every row keeps its `source_row_id`.
5. **Calendarize.** Each bill's kWh and cost are split across the months it covers, by days. Billing periods are [start, end): the end date is not counted.
6. **Reconcile.** A bridge from the raw file to raw 2024 to clean 2024, tied to the kWh and the dollar.

## What I found

| # | Issue | Size (2024) | Treatment |
|---|---|---|---|
| 1 | Estimated reads never replaced by actuals | 14.6% of kWh; 149 meters estimated all year (5.2%) | Kept as reported, flagged; actual reads requested |
| 2 | Demand-only meter rows (kW, no kWh) | 17,900 rows; no kWh effect | 17,093 paired and their cost merged into the energy meter (same bill and building, same last 6 digits) |
| 3 | Energy charged but no kWh recorded | 220 bills, 60 meters; ~4.35M kWh implied (0.4%) | Filled from charges / typical $/kWh, flagged; source bills requested |
| 4 | Same meter and period billed twice (Jan-Feb 2025 batch) | 108 pairs; 31 conflicting | Empty rows dropped; conflicts keep the later bill (-112,557 kWh, -$6,205) |
| 5 | Overlapping billing periods | 21 pairs, ~0.09% of kWh | Kept, disclosed as immaterial |
| 6 | Partial-year meters | 257 meters under 300 days (1.5% of kWh) | Reported per site, not gap-filled |
| 7 | Invalid periods (days <= 0 or > 45) | 8 rows, 0 kWh | Excluded |
| 8 | Site names and borough change between bills | 122 meters renamed (5.5% of kWh); 2,510 rows with a conflicting borough | One site key per meter (RC code), one name and borough per site |
| 9 | Excel errors exported as data | 2,686 rows with `#REF!` / `#N/A` in `amp` | Kept as text, raised as an export fix |

**Plot twist:** calendarizing barely moves the annual total (+0.34% vs grouping by revenue month), but it moves up to 13.2M kWh between months. May is 17.7% higher once bills are split by days. Annual reports would never notice; monthly or quarterly reports would be wrong.

## Reconciliation

| Step | kWh | $ |
|---|---:|---:|
| Raw 2024, calendarized | 1,114,820,684 | 185,977,473 |
| less: duplicate rows dropped | -112,557 | -6,205 |
| demand-only cost moved to energy rows | 0 | 0 (net) |
| plus: implied kWh on bills with no kWh recorded | +4,350,151 | 0 |
| **Clean 2024** | **1,119,058,278** | **185,971,268** |

Every check cell in the workbook reads 0: expected vs calendarized totals, raw calendarization vs prorated formulas, and clean activity vs kept plus filled rows.

## Power Query

| Query | What it does |
|---|---|
| [`Raw_flagged`](queries/05_Raw_flagged.pq) | Types the raw table, adds the demand-only, kWh-missing and estimated flags as custom columns, flags duplicates by merging in `dup_keys` (left outer join on meter + start + end), and checks every flag against the source flags |
| [`dup_keys`](queries/04_dup_keys.pq) | Groups by meter + start + end to count rows per billing period |
| [`Clean_Activity`](queries/01_Clean_Activity.pq) | Reads the clean activity table and types the period columns |
| [`ReportYear`](queries/02_ReportYear.pq) | Parameter for the reporting year |
| [`Calendarized_2024`](queries/03_Calendarized_2024.pq) | Expands each bill into the months it touches, prorates kWh and cost by days, groups by site and month |

**Checks:** the Power Query flags match on all 51,854 rows (17,900 demand-only, 223 kWh missing, 7,017 estimated, 216 duplicate rows; 0 rows differ), and `Calendarized_2024` matches the Reconciliation totals.

## Workbook tabs

| Tab | What it holds |
|---|---|
| Issues log | Every issue with its detection rule, row counts and 2024 kWh (live COUNTIFS / SUMIFS) |
| Reconciliation | Raw to clean bridge, check cells, coverage per site |
| Decision log | Options considered, choice, reason, kWh / $ effect, question for the customer |
| Calendarized_2024 | Live Power Query output by site and month |
| Raw_flagged | Live Power Query flags and the row-by-row match check |
| Clean activity | The activity template: one row per bill x meter kept, with source IDs and treatment |
| Raw | Source columns as downloaded, plus derived proration, flag and treatment columns |
| Profile · Site map · Calendarized monthly · PQ code | First look at the data, one site per meter, monthly comparison, M code reference |

## How this was built

Initial profiling and flagging were scripted in Python for speed. The logic a team would refresh or a verifier would follow lives in Excel: Power Query rebuilds the four main issue flags and the calendarization, and both match the scripted results on every row and to the dollar. The profiling script is in [`scripts/`](scripts/) and reprints every headline number above from the raw CSV in about two seconds.

## Reproduce it

```bash
# 1. Download the raw data (see data/README.md for the exact query)
# 2. Reprint the headline numbers
pip install -r requirements.txt
python3 scripts/nycha_profile.py data/nycha_elec_2024_raw.csv
```

Then open the workbook, go to **Data > Get Data (Power Query) > Launch Power Query Editor**, and click through the Applied Steps of `Raw_flagged` and `Calendarized_2024`.

## Repository map

```
docs/NYCHA_CY2024_customer_memo.pdf   customer-facing memo (start here)
queries/*.pq                          Power Query M for all five queries
scripts/nycha_profile.py              profiling script: tie-out, grain, issue sizes, monthly calendarization
screenshots/                          Power Query steps, reconciliation checks, issues log
data/README.md                        how to pull the source data (CSV not committed)
```

The workbook (21 MB) is attached to the [latest release](../../releases/latest).

---

*Self-directed sample on public data. NYCHA is used as a mock customer; this is not client work. The activity layout follows publicly documented integration fields and is not any vendor's actual template.*
