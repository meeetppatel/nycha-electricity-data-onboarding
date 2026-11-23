"""
NYCHA electricity CY2024: profile, flag and calendarize the raw export.

Run:  python3 scripts/nycha_profile.py data/nycha_elec_2024_raw.csv

Each section prints the numbers it produces, so you can check them against
the workbook (Profile, Issues log, Reconciliation).
"""
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# 1. LOAD: read every column as text first, then convert only what needs it.
#    Same idea as the Power Query type step: IDs stay text (some contain
#    letters, e.g. 9863107_S011600-87.8%), amounts become numbers.
# ---------------------------------------------------------------------------
path = sys.argv[1]
df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
df.insert(0, "source_row_id", range(1, len(df) + 1))   # traceability key

for col in ["days", "current_charges", "consumption_kwh", "kwh_charges",
            "consumption_kw", "kw_charges", "other_charges"]:
    df[col] = pd.to_numeric(df[col])
for col in ["service_start_date", "service_end_date"]:
    df[col] = pd.to_datetime(df[col]).dt.normalize()     # drop the time part

print("== 1. Tie-out to the source file")
print(f"rows            {len(df):,}")
print(f"kWh             {df.consumption_kwh.sum():,.2f}")
print(f"charges         ${df.current_charges.sum():,.2f}")

# ---------------------------------------------------------------------------
# 2. GRAIN: what is one row?  If bill + meter never repeats, one row is
#    one bill x one meter.
# ---------------------------------------------------------------------------
print("\n== 2. Grain")
print("max rows per bill + meter:", df.groupby(["umis_bill_id", "meter_number"]).size().max())
print("max rows per bill:        ", df.groupby("umis_bill_id").size().max())

# ---------------------------------------------------------------------------
# 3. CY2024 SHARE OF EACH BILL: periods are [start, end), end not counted.
#    days_2024 = overlap of the bill with 2024; kWh is prorated by days.
#    Bills with days <= 0 or > 45 are invalid and not prorated.
# ---------------------------------------------------------------------------
Y0, Y1 = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-01-01")
df["valid_period"] = (df.days > 0) & (df.days <= 45)
start = df.service_start_date.clip(lower=Y0)
end = df.service_end_date.clip(upper=Y1)
df["days_2024"] = (end - start).dt.days.clip(lower=0).where(df.valid_period, 0)
share = (df.days_2024 / df.days).where(df.valid_period, 0)
df["kwh_2024"] = df.consumption_kwh * share
df["cost_2024"] = df.current_charges * share
TOTAL = df.kwh_2024.sum()

print("\n== 3. CY2024 calendarized (raw, before cleaning)")
print(f"kWh             {TOTAL:,.0f}")
print(f"charges         ${df.cost_2024.sum():,.0f}")

# ---------------------------------------------------------------------------
# 4. FLAGS: one TRUE/FALSE column per issue rule (same rules as Raw_flagged).
# ---------------------------------------------------------------------------
df["flag_est"] = df.estimated.eq("Y")
df["flag_demand_only"] = df.consumption_kwh.eq(0) & df.consumption_kw.gt(0)
df["flag_kwh_missing"] = df.consumption_kwh.eq(0) & df.kwh_charges.gt(0)
key = ["meter_number", "service_start_date", "service_end_date"]
df["flag_dup"] = df.duplicated(key, keep=False)          # same meter + period twice
df["flag_bad_days"] = ~df.valid_period

print("\n== 4. Issue sizes")
for flag in ["flag_est", "flag_demand_only", "flag_kwh_missing", "flag_dup", "flag_bad_days"]:
    rows = df[flag].sum()
    kwh = df.loc[df[flag], "kwh_2024"].sum()
    print(f"{flag:18s} rows {rows:6,}   CY2024 kWh {kwh:15,.0f}   {kwh / TOTAL:6.2%}")

# Meters estimated on every 2024 bill (and carrying kWh)
t24 = df[df.days_2024 > 0]
m = t24.groupby("meter_number").agg(all_est=("flag_est", "all"), kwh=("kwh_2024", "sum"))
all_est = m[m.all_est & (m.kwh > 0)]
print(f"meters estimated all year: {len(all_est)}  ({all_est.kwh.sum() / TOTAL:.2%} of kWh)")

# ---------------------------------------------------------------------------
# 5. DEMAND-ONLY PAIRING: the kW-only meter and its kWh meter sit on the same
#    bill + location and share their last 6 digits (e.g. 1376868 / 4376868).
# ---------------------------------------------------------------------------
dem = df[df.flag_demand_only][["umis_bill_id", "location", "meter_number"]]
eng = df[df.consumption_kwh > 0][["umis_bill_id", "location", "meter_number"]]
pairs = dem.assign(t6=dem.meter_number.str[-6:]).merge(
    eng.assign(t6=eng.meter_number.str[-6:]), on=["umis_bill_id", "location", "t6"])
print(f"\n== 5. Demand-only rows with an energy partner (same bill, location, last 6 digits): "
      f"{pairs.meter_number_x.count():,} of {len(dem):,}")

# ---------------------------------------------------------------------------
# 6. MONTHLY CALENDARIZATION: split each bill into the months it touches,
#    prorate by days (the same logic as the Calendarized_2024 query).
# ---------------------------------------------------------------------------
rows = []
for r in df[df.valid_period].itertuples():
    month = r.service_start_date.replace(day=1)
    while month < r.service_end_date:
        nxt = month + pd.offsets.MonthBegin(1)
        d = (min(r.service_end_date, nxt) - max(r.service_start_date, month)).days
        if d > 0 and month.year == 2024:
            rows.append((month, r.consumption_kwh * d / r.days))
        month = nxt
monthly = pd.DataFrame(rows, columns=["month", "kwh"]).groupby("month").kwh.sum()
by_rev = df[df.revenue_month.str.startswith("2024")].groupby("revenue_month").consumption_kwh.sum()

print("\n== 6. CY2024 by month: calendarized vs revenue_month")
for month, kwh in monthly.items():
    rev = by_rev.get(month.strftime("%Y-%m"), 0)
    print(f"{month:%Y-%m}  {kwh:13,.0f}  {rev:13,.0f}  {kwh / rev - 1:+6.1%}")
print(f"total    {monthly.sum():13,.0f}  {by_rev.sum():13,.0f}  {monthly.sum() / by_rev.sum() - 1:+6.2%}")
