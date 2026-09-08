# VRPTW data

Solomon VRPTW benchmark instances ([Kaggle source](https://www.kaggle.com/datasets/masud7866/solomon-vrptw-benchmark)).

## CSV schema

Each instance is a CSV with one row per customer (including the depot). Required columns:

| Column | Description |
|---|---|
| `cust_no` | Customer ID (`0` or `1` for the depot) |
| `xcoord` | X coordinate |
| `ycoord` | Y coordinate |
| `demand` | Demand (0 for the depot) |
| `ready_time` | Earliest service start |
| `due_date` | Latest service start |
| `service_time` | Service duration |

Column headers are normalized on ingest (lowercase, spaces → underscores, periods removed), so headers like `CUST NO.` and `READY TIME` work as-is.

## Directory layout

```
data/
  <dataset_name>/
    <instance>.csv
```

Example: `data/solomon/C1/C101.csv` → dataset `solomon`, instance `C101`.

## Database upload

On `docker compose up`, the `db-init` service runs `db/ingest.py`, which:

1. Recursively finds every `*.csv` under `data/`.
2. Upserts a row in `datasets` (keyed by `name` + `instance`).
3. Upserts customer rows in `instances`.

To reload after changing CSVs:

```bash
docker compose down -v
docker compose up
```

The `-v` flag drops the Postgres volume so schema and data are recreated from scratch.
