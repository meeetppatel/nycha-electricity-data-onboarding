# Source data

**Dataset:** NYCHA Electric Consumption And Cost (2010 - Sep 2025), NYC Open Data id `jr24-e7cr`, last updated Feb 9, 2026.
Catalog: https://catalog.data.gov/dataset/electric-consumption-and-cost-2010-may-2025

The CSV is not committed. Pull it with the same filter used in this project (bills that touch 2024, plus a one-month buffer on each side):

```bash
curl -sS -G "https://data.cityofnewyork.us/resource/jr24-e7cr.csv" \
  --data-urlencode "\$where=service_end_date >= '2023-12-01' AND service_start_date < '2025-02-01'" \
  --data-urlencode "\$limit=200000" \
  -o data/nycha_elec_2024_raw.csv
```

Or paste this into a browser and save the file as `nycha_elec_2024_raw.csv`:

```
https://data.cityofnewyork.us/resource/jr24-e7cr.csv?$where=service_end_date%20%3E%3D%20%272023-12-01%27%20AND%20service_start_date%20%3C%20%272025-02-01%27&$limit=200000
```

**Expected tie-out:** 51,854 rows · 1,374,104,258.56 kWh · $226,136,812.49.
The source is refreshed periodically, so a later pull may differ slightly.
