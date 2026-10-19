import hashlib
import json
import time
from pathlib import Path

import pandas as pd
from pygeohydro import WaterQuality

WQ_GAGES_DIR = PROJECT_DIR / "raw" / "gagesii_wq"
BATCH_DIR = WQ_GAGES_DIR / "batches"
BATCH_DIR.mkdir(parents=True, exist_ok=True)

ids = (
    gages_conus["STAID"]
    .astype("string")
    .str.strip()
    .str.removeprefix("USGS-")
)

# Inspect missing or nonnumeric identifiers
invalid = ids.isna() | ~ids.str.fullmatch(r"\d+", na=False)

if invalid.any():
    display(gages_conus.loc[invalid, ["STAID", "STANAME"]])
    raise ValueError("Review the identifiers shown above.")

# Restore leading zeros for short IDs; preserve longer IDs
station_ids = sorted(ids.str.zfill(8).unique().tolist())

print("Gauges prepared:", len(station_ids))
print("ID lengths:")
print(pd.Series(station_ids).str.len().value_counts().sort_index())
print("Longer IDs:", [s for s in station_ids if len(s) > 8][:10])
assert all(s.isdigit() and 8 <= len(s) <= 15 for s in station_ids)
assert len(station_ids) == len(set(station_ids))

query = {
    "pCode": "00010;00300;00618;71851;00631",
    "startDateLo": "01-01-1980",
    "startDateHi": "12-31-2024",
}

wqp = WaterQuality()
BATCH_SIZE = 25
status_rows = []

for start in range(0, len(station_ids), BATCH_SIZE):
    batch = station_ids[start:start + BATCH_SIZE]
    batch_number = start // BATCH_SIZE + 1

    # Cache identity includes exact station IDs and query settings
    signature = json.dumps(
        {"stations": batch, "query": query},
        sort_keys=True,
    )
    key = hashlib.sha256(signature.encode()).hexdigest()[:16]

    data_file = BATCH_DIR / f"{key}.parquet"
    marker_file = BATCH_DIR / f"{key}.json"

    # Skip only requests previously completed successfully
    if marker_file.exists():
        marker = json.loads(marker_file.read_text())
        if data_file.exists():
            status_rows.append(marker)
            continue

    for attempt in range(1, 4):
        try:
            raw = wqp.data_bystation(
                ["USGS-" + sid for sid in batch],
                query,
            )

            if raw is None:
                raise RuntimeError("Request returned None.")

            raw.columns = raw.columns.astype(str).str.strip()

            # Save atomically so an interrupted write isn't reused
            temporary = data_file.with_suffix(".tmp")
            raw.to_parquet(temporary, index=False)
            temporary.replace(data_file)

            marker = {
                "batch": batch_number,
                "key": key,
                "status": "complete",
                "requested_gauges": len(batch),
                "raw_records": len(raw),
                "stations": batch,
                "query": query,
            }

            marker_file.write_text(json.dumps(marker, indent=2))
            status_rows.append(marker)

            print(
                f"Batch {batch_number}: {len(raw):,} records "
                f"from {len(batch)} requested gauges",
                flush=True,
            )
            break

        except Exception as exc:
            print(
                f"Batch {batch_number}, attempt {attempt}: {exc}",
                flush=True,
            )

            if attempt == 3:
                status_rows.append({
                    "batch": batch_number,
                    "key": key,
                    "status": "failed",
                    "requested_gauges": len(batch),
                    "error": str(exc),
                })
            else:
                time.sleep(5 * attempt)

    # Keep requests sequential and give the service a short pause
    time.sleep(1)

download_status = pd.DataFrame(status_rows)
download_status.to_csv(
    WQ_GAGES_DIR / "download_status.csv",
    index=False,
)

print("\nDownload summary:")
print(download_status["status"].value_counts())

print(
    "Raw records in completed batches:",
    int(download_status.loc[
        download_status["status"] == "complete",
        "raw_records",
    ].sum()),
)

display(download_status[
    download_status["status"] == "failed"
])
