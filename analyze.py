#!/usr/bin/env python3
"""
Indego bike share — growth analysis
=====================================
Data: quarterly anonymised trip files published by the City of Philadelphia /
Bicycle Transit Systems on Indego's program website, https://www.rideindego.com/about/data/
plus the Station Table published on the same page (updated 2026-10-15).

What this script does
---------------------
1. Loads every quarterly trip file from 2015 Q2 (launch, April 2015) through
   2026 Q3 (latest published). If a file is missing locally it is downloaded
   from rideindego.com (browser-style headers are required: the site's
   Cloudflare layer returns 403 to bare curl) and unzipped.
2. Aggregates per quarter and per year: trips, total trip-minutes (the
   revenue proxy — the challenge states revenue is primarily driven by trip
   duration), mean/median duration, passholder mix, e-bike share, distinct
   bikes and stations used.
3. Reconstructs station supply over time from the Station Table's go-live
   dates, and computes trips per active station (demand vs supply).
4. Writes tables to outputs/ and charts to outputs/charts/, and prints the
   headline numbers used in the slide deck and README.

Caveats (see README.md for the full list)
------------------------------------------
- 2015 is a partial year (system launched 23 April 2015); 2026 covers
  Jan–Sep only (Q4 not yet published). Year-on-year comparisons use
  like-for-like quarters.
- The trip files contain no prices, revenue, costs, membership counts or
  bike-fleet size. Trip-minutes are a *proxy* for revenue, not revenue.
- Passholder_type labels changed over the years (e.g. "Indego30",
  "Indego365", "Indego365 Plus", "Guest Pass", "Walk-up"); the script groups
  them into Passholder (30/365/365 Plus/ACCESS/corporate) vs Casual
  (Walk-up single ride + Guest Pass) using the labels present in each file.
- bike_type (standard vs electric) is only recorded from 2018 onwards.
- The data page says duration is in minutes, but the files from 2015Q2
  through 2017Q2 actually record it in seconds (median ~600-900, max
  86,400 = 24h in seconds); from 2017Q3 on it is minutes (max 1,440).
  The script detects the unit per file (median > 60 -> seconds) and
  converts. Without this, pre-2018 trip-minutes are overstated ~60x.
- Duration is capped at 24 hours by the publisher; trips under 1 minute
  were removed by the publisher before release.

Requirements: pandas, matplotlib (see requirements.txt).
Run:  python3 analyze.py        (from the repo root; data/ may be empty —
       the script downloads what it needs, ~200 MB of zips)
"""

import csv
import os
import re
import subprocess
import sys
import zipfile
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXTRACT_DIR = os.path.join(DATA_DIR, "extracted")
OUT_DIR = os.path.join(BASE_DIR, "outputs")
CHART_DIR = os.path.join(OUT_DIR, "charts")
STATION_TABLE = os.path.join(DATA_DIR, "indego-stations-2026-10-15.csv")
STATION_TABLE_URL = (
    "https://www.rideindego.com/wp-content/uploads/2026/10/indego-stations-2026-10-15.csv"
)
DATA_PAGE = "https://www.rideindego.com/about/data/"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# (quarter label, csv file inside data/extracted, zip file, download URL)
# URLs are the links published on https://www.rideindego.com/about/data/
QUARTERS = [
    ("2015Q2", "Indego_Trips_2015Q2.csv", "Indego_Trips_2015Q2.zip",
     "http://www.rideindego.com/wp-content/uploads/2016/01/Indego_Trips_2015Q2.zip"),
    ("2015Q3", "Indego_Trips_2015Q3.csv", "Indego_Trips_2015Q3.zip",
     "http://www.rideindego.com/wp-content/uploads/2016/01/Indego_Trips_2015Q3.zip"),
    ("2015Q4", "Indego_Trips_2015Q4.csv", "Indego_Trips_2015Q4.zip",
     "http://www.rideindego.com/wp-content/uploads/2016/01/Indego_Trips_2015Q4.zip"),
    ("2016Q1", "Indego_Trips_2016Q1.csv", "Indego_Trips_2016Q1.zip",
     "https://www.rideindego.com/wp-content/uploads/2016/07/Indego_Trips_2016Q1.zip"),
    ("2016Q2", "Indego_Trips_2016Q2.csv", "Indego_Trips_2016Q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2016/07/Indego_Trips_2016Q2.zip"),
    ("2016Q3", "Q3_2016_trips.csv", "Q3_2016_trips.zip",
     "https://www.rideindego.com/wp-content/uploads/2016/10/Q3_2016_trips.zip"),
    ("2016Q4", "Indego_trips_Q4_2016.csv", "Indego_trips_Q4_2016.zip",
     "https://www.rideindego.com/wp-content/uploads/2017/01/Indego_trips_Q4_2016.zip"),
    ("2017Q1", "indego_gbfs_trips_Q1_2017.csv", "indego_gbfs_trips_Q1_2017.zip",
     "https://www.rideindego.com/wp-content/uploads/2017/04/indego_gbfs_trips_Q1_2017.zip"),
    ("2017Q2", "indego_gbfs_trips_Q2_2017.csv", "indego_gbfs_trips_Q2_2017.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2017/07/indego_gbfs_trips_Q2_2017.csv.zip"),
    ("2017Q3", "indego-trips-2017-q3.csv", "indego-trips-2017-q3.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2015/12/indego-trips-2017-q3.csv.zip"),
    # NOTE: the 2017-Q4 zip contains a file with an odd internal name
    # ("indego-quarter-echo.bicycletransit.com-2018-01-19-9-57 AM.csv");
    # it is the 2017 Q4 data (first trip 2017-10-01).
    ("2017Q4", "indego-quarter-echo.bicycletransit.com-2018-01-19-9-57 AM.csv",
     "indego-trips-2017-q4.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2018/01/indego-trips-2017-q4.csv.zip"),
    ("2018Q1", "indego-trips-2018-q1.csv", "indego-trips-2018-q1.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2018/04/indego-trips-2018-q1.csv.zip"),
    ("2018Q2", "indego-trips-2018-q2.csv", "indego-trips-2018-q2.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2018/09/indego-trips-2018-q2.csv.zip"),
    ("2018Q3", "indego-trips-2018-q3.csv", "indego-trips-2018-q3.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2019/01/indego-trips-2018-q3.csv.zip"),
    ("2018Q4", "indego-trips-2018-q4.csv", "indego-trips-2018-q4.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2019/01/indego-trips-2018-q4.csv.zip"),
    ("2019Q1", "indego-trips-2019-q1.csv", "indego-trips-2019-q1.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2019/04/indego-trips-2019-q1.csv.zip"),
    ("2019Q2", "indego-trips-2019-q2.csv", "indego-trips-2019-q2.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2019/07/indego-trips-2019-q2.csv.zip"),
    ("2019Q3", "indego-trips-2019-q3.csv", "indego-trips-2019-q3-1.zip",
     "https://www.rideindego.com/wp-content/uploads/2019/10/indego-trips-2019-q3-1.zip"),
    ("2019Q4", "indego-trips-2019-q4.csv", "indego-trips-2019-q4.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2020/01/indego-trips-2019-q4.csv.zip"),
    ("2020Q1", "indego-trips-2020-q1.csv", "indego-trips-2020-q1.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2020/04/indego-trips-2020-q1.csv.zip"),
    ("2020Q2", "indego-trips-2020-q2.csv", "indego-trips-2020-q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2020/08/indego-trips-2020-q2.zip"),
    ("2020Q3", "indego-trips-2020-q3.csv", "indego-trips-2020-q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2020/10/indego-trips-2020-q3.zip"),
    ("2020Q4", "indego-trips-2020-q4.csv", "indego-trips-2020-q4.zip",
     "https://www.rideindego.com/wp-content/uploads/2021/01/indego-trips-2020-q4.zip"),
    ("2021Q1", "indego-trips-2021-q1.csv", "indego-trips-2021-q1.zip",
     "https://www.rideindego.com/wp-content/uploads/2021/04/indego-trips-2021-q1.zip"),
    ("2021Q2", "indego-trips-2021-q2.csv", "indego-trips-2021-q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2021/07/indego-trips-2021-q2.zip"),
    ("2021Q3", "indego-trips-2021-q3.csv", "indego-trips-2021-q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2021/10/indego-trips-2021-q3.zip"),
    ("2021Q4", "indego-trips-2021-q4.csv", "indego-trips-2021-q4.zip",
     "https://www.rideindego.com/wp-content/uploads/2022/01/indego-trips-2021-q4.zip"),
    ("2022Q1", "indego-trips-2022-q1.csv", "indego-trips-2022-q1.zip",
     "https://www.rideindego.com/wp-content/uploads/2022/04/indego-trips-2022-q1.zip"),
    ("2022Q2", "indego-trips-2022-q2.csv", "indego-trips-2022-q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2022/07/indego-trips-2022-q2.zip"),
    ("2022Q3", "indego-trips-2022-q3.csv", "indego-trips-2022-q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2022/12/indego-trips-2022-q3.zip"),
    ("2022Q4", "indego-trips-2022-q4.csv", "indego-trips-2022-q4.zip",
     "https://www.rideindego.com/wp-content/uploads/2023/01/indego-trips-2022-q4.zip"),
    ("2023Q1", "indego-trips-2023-q1.csv", "indego-trips-2023-q1.zip",
     "https://www.rideindego.com/wp-content/uploads/2023/04/indego-trips-2023-q1.zip"),
    ("2023Q2", "indego-trips-2023-q2.csv", "indego-trips-2023-q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2023/07/indego-trips-2023-q2.zip"),
    ("2023Q3", "indego-trips-2023-q3-2.csv", "indego-trips-2023-q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2023/10/indego-trips-2023-q3.zip"),
    ("2023Q4", "indego-trips-2023-q4.csv", "indego-trips-2023-q4.zip",
     "https://www.rideindego.com/wp-content/uploads/2024/01/indego-trips-2023-q4.zip"),
    ("2024Q1", "indego-trips-2024-q1.csv", "indego-trips-2024-q1.zip",
     "https://www.rideindego.com/wp-content/uploads/2024/04/indego-trips-2024-q1.zip"),
    ("2024Q2", "indego-trips-2024-q2.csv", "indego-trips-2024-q2.zip",
     "https://www.rideindego.com/wp-content/uploads/2024/07/indego-trips-2024-q2.zip"),
    ("2024Q3", "indego-trips-2024-q3.csv", "indego-trips-2024-q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2024/10/indego-trips-2024-q3.zip"),
    ("2024Q4", "indego-trips-2024-q4.csv", "indego-trips-2024-q4.zip",
     "https://www.rideindego.com/wp-content/uploads/2025/01/indego-trips-2024-q4.zip"),
    ("2025Q1", "indego-trips-2025-q1.csv", "indego-trips-2025-q1.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2025/04/indego-trips-2025-q1.zip"),
    ("2025Q2", "indego-trips-2025-q2.csv", "indego-trips-2025-q2.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2025/07/indego-trips-2025-q2.zip"),
    ("2025Q3", "indego-trips-2025-q3.csv", "indego-trips-2025-q3.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2025/10/indego-trips-2025-q3.zip"),
    ("2025Q4", "indego-trips-2025-q4.csv", "indego-trips-2025-q4.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2026/01/indego-trips-2025-q4.zip"),
    ("2026Q1", "indego-trips-2026-q1.csv", "indego-trips-2026-q1.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2026/04/indego-trips-2026-q1.zip"),
    ("2026Q2", "indego-trips-2026-q2.csv", "indego-trips-2026-q2.csv.zip",
     "https://www.rideindego.com/wp-content/uploads/2026/07/indego-trips-2026-q2.zip"),
    ("2026Q3", "indego-trips-2026-Q3.csv", "indego-trips-2026-Q3.zip",
     "https://www.rideindego.com/wp-content/uploads/2026/10/indego-trips-2026-Q3.zip"),
]

# Passholder labels that count as "casual" (pay-per-ride / visitor) rather than
# a subscription pass. Everything else is treated as a passholder. Labels are
# matched case-insensitively and by substring so historical label variants
# (e.g. "Walk-up", "Guest Pass", "Day Pass") are all caught.
CASUAL_MARKERS = ("walk", "guest", "day pass", "single ride", "casual")


def classify_passholder(label):
    """Return 'Casual' or 'Passholder' for a passholder_type value."""
    if label is None or (isinstance(label, float) and pd.isna(label)):
        return "Unknown"
    low = str(label).strip().lower()
    if any(m in low for m in CASUAL_MARKERS):
        return "Casual"
    return "Passholder"


def ensure_file(quarter, csv_name, zip_name, url):
    """Make sure the extracted CSV exists; download + unzip if needed."""
    path = os.path.join(EXTRACT_DIR, csv_name)
    if os.path.exists(path):
        return path
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    zip_path = os.path.join(DATA_DIR, zip_name)
    if not os.path.exists(zip_path):
        print(f"  downloading {quarter} ...", flush=True)
        subprocess.run(
            ["curl", "-sL", "--max-time", "600", "-A", UA,
             "-H", f"Referer: {DATA_PAGE}", "-H", "Accept: */*",
             "-o", zip_path, url],
            check=True,
        )
    with zipfile.ZipFile(zip_path) as zf:
        # extract only the trip csv (zips occasionally bundle old station tables)
        for name in zf.namelist():
            if name.startswith("__MACOSX"):
                continue
            if name.lower().endswith(".csv") and "station" not in name.lower():
                zf.extract(name, EXTRACT_DIR)
    if not os.path.exists(path):
        # fall back: take whatever trip csv the zip contained
        cands = [f for f in os.listdir(EXTRACT_DIR)
                 if f.lower().endswith(".csv") and "station" not in f.lower()]
        raise FileNotFoundError(f"{quarter}: expected {csv_name}, found {cands}")
    return path


def load_quarter(path):
    """Read one quarterly file; return per-quarter aggregates + monthly rows."""
    # Column names vary slightly by vintage (start_station_id vs start_station,
    # quoted headers in 2018-19, bike_type absent before 2018).
    df = pd.read_csv(
        path,
        usecols=lambda c: c.strip().lower() in {
            "duration", "start_time", "passholder_type", "bike_type",
            "bike_id", "start_station", "start_station_id",
        },
        low_memory=False,
    )
    df.columns = [c.strip().lower() for c in df.columns]
    if "start_station_id" in df.columns:
        df = df.rename(columns={"start_station_id": "start_station"})
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df = df.dropna(subset=["start_time"])
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df = df.dropna(subset=["duration"])
    df = df[df["duration"] > 0]  # publisher already removes <1 min trips
    # SCHEMA QUIRK (verified from the files): the data page says duration is
    # in minutes, but files from 2015Q2 through 2017Q2 record it in SECONDS
    # (median ~600-900, max 86,400 = 24h in seconds). From 2017Q3 on it is
    # minutes (median ~10-20, max 1,440 = 24h in minutes). Detect per file.
    duration_unit = "seconds" if df["duration"].median() > 60 else "minutes"
    if duration_unit == "seconds":
        df["duration"] = df["duration"] / 60.0
    df["month"] = df["start_time"].dt.to_period("M")
    df["pass_group"] = df["passholder_type"].map(classify_passholder)

    monthly = (
        df.groupby("month")
        .agg(trips=("duration", "size"), trip_minutes=("duration", "sum"))
        .reset_index()
    )
    monthly["month"] = monthly["month"].dt.to_timestamp()

    agg = {
        "duration_unit_in_file": duration_unit,
        "trips": len(df),
        "trip_minutes": float(df["duration"].sum()),
        "mean_duration_min": float(df["duration"].mean()),
        "median_duration_min": float(df["duration"].median()),
        "trips_over_30min": int((df["duration"] > 30).sum()),
        "trips_over_60min": int((df["duration"] > 60).sum()),
        "distinct_bikes": int(df["bike_id"].nunique()) if "bike_id" in df else None,
        "distinct_start_stations": int(df["start_station"].nunique())
        if "start_station" in df else None,
        "passholder_trips": int((df["pass_group"] == "Passholder").sum()),
        "casual_trips": int((df["pass_group"] == "Casual").sum()),
        "unknown_pass_trips": int((df["pass_group"] == "Unknown").sum()),
    }
    if "bike_type" in df.columns:
        bt = df["bike_type"].astype(str).str.lower()
        agg["ebike_trips"] = int(bt.str.contains("electric").sum())
        agg["standard_trips"] = int(bt.str.contains("standard").sum())
    else:
        agg["ebike_trips"] = None
        agg["standard_trips"] = None
    return agg, monthly, df["passholder_type"].value_counts().to_dict()


def station_growth():
    """Cumulative stations opened by year-end, from go-live dates.

    Two series: (a) all stations ever opened (by go-live date, regardless of
    current status) and (b) stations still Active as of the 2026-10-15 table.
    Note the table cannot tell us when a station went inactive, so (b) is a
    lower bound on the active count in earlier years.
    """
    if not os.path.exists(STATION_TABLE):
        subprocess.run(
            ["curl", "-sL", "--max-time", "300", "-A", UA,
             "-H", f"Referer: {DATA_PAGE}",
             "-o", STATION_TABLE, STATION_TABLE_URL],
            check=True,
        )
    st = pd.read_csv(STATION_TABLE)
    st.columns = [c.strip() for c in st.columns]
    date_col = [c for c in st.columns if "go_live" in c.lower() or "Go_live" in c][0]
    st["go_live"] = pd.to_datetime(st[date_col], errors="coerce")
    st = st.dropna(subset=["go_live"])
    st["year"] = st["go_live"].dt.year
    rows = []
    for y in range(2015, 2027):
        opened = st[st["year"] <= y]
        active = opened[opened["Status"].str.lower() == "active"] \
            if "Status" in opened else opened
        rows.append({
            "year": y,
            "stations_opened_cum": len(opened),
            "stations_active_asof_oct2026": len(active),
            "stations_opened_in_year": int((st["year"] == y).sum()),
        })
    return pd.DataFrame(rows), st


def cagr(start, end, years):
    return (end / start) ** (1 / years) - 1


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CHART_DIR, exist_ok=True)

    q_rows, monthly_all, label_counts = [], [], defaultdict(int)
    for quarter, csv_name, zip_name, url in QUARTERS:
        path = ensure_file(quarter, csv_name, zip_name, url)
        agg, monthly, labels = load_quarter(path)
        for k, v in labels.items():
            label_counts[k] += v
        agg["quarter"] = quarter
        agg["year"] = int(quarter[:4])
        q_rows.append(agg)
        monthly["quarter"] = quarter
        monthly_all.append(monthly)
        print(f"{quarter}: {agg['trips']:,} trips, "
              f"{agg['trip_minutes']:,.0f} trip-min, "
              f"mean {agg['mean_duration_min']:.1f} min", flush=True)

    q = pd.DataFrame(q_rows).sort_values("quarter")
    q["casual_share"] = q["casual_trips"] / q["trips"]
    q["ebike_share"] = q["ebike_trips"] / q["trips"]
    q["trips_yoy"] = q["trips"].pct_change(4)  # same quarter last year
    q["minutes_yoy"] = q["trip_minutes"].pct_change(4)
    q.to_csv(os.path.join(OUT_DIR, "quarterly_summary.csv"), index=False)

    monthly = pd.concat(monthly_all).sort_values("month")
    monthly.to_csv(os.path.join(OUT_DIR, "monthly_summary.csv"), index=False)

    annual = (
        q.groupby("year")
        .agg(trips=("trips", "sum"), trip_minutes=("trip_minutes", "sum"),
             median_duration_min=("median_duration_min", "median"),
             passholder_trips=("passholder_trips", "sum"),
             casual_trips=("casual_trips", "sum"),
             ebike_trips=("ebike_trips", "sum"),
             distinct_bikes_max_qtr=("distinct_bikes", "max"),
             distinct_start_stations_max_qtr=("distinct_start_stations", "max"),
             quarters=("quarter", "count"))
        .reset_index()
    )
    # overall mean duration = total minutes / total trips (not mean of means)
    annual["mean_duration_min"] = annual["trip_minutes"] / annual["trips"]
    annual["trips_yoy"] = annual["trips"].pct_change()
    annual["minutes_yoy"] = annual["trip_minutes"].pct_change()
    annual["casual_share"] = annual["casual_trips"] / annual["trips"]
    annual["ebike_share"] = annual["ebike_trips"] / annual["trips"]
    annual.to_csv(os.path.join(OUT_DIR, "annual_summary.csv"), index=False)

    stations, st_raw = station_growth()
    stations.to_csv(os.path.join(OUT_DIR, "station_growth.csv"), index=False)
    annual = annual.merge(
        stations[["year", "stations_opened_cum", "stations_active_asof_oct2026"]],
        on="year", how="left")
    annual["trips_per_station"] = annual["trips"] / annual["stations_opened_cum"]

    print("\n=== passholder_type labels seen (all years) ===")
    for k, v in sorted(label_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k!r}: {v:,}")
    print("\n=== annual summary ===")
    print(annual.to_string(index=False))
    print("\n=== quarterly YoY (2023Q1 onwards) ===")
    print(q[q["quarter"] >= "2023Q1"][["quarter", "trips", "trips_yoy",
                                        "trip_minutes", "minutes_yoy",
                                        "casual_share", "ebike_share"]]
          .to_string(index=False))

    # ---- daily peaks, 2025-2026 (peak-day load: the "too fast?" test) ----
    daily_frames = []
    for quarter, csv_name, zip_name, url in QUARTERS:
        if quarter < "2025Q1":
            continue
        path = os.path.join(EXTRACT_DIR, csv_name)
        d = pd.read_csv(path, usecols=["start_time"])
        d["date"] = pd.to_datetime(d["start_time"], errors="coerce").dt.date
        daily_frames.append(d.groupby("date").size().rename("trips").reset_index())
    daily = pd.concat(daily_frames).groupby("date", as_index=False)["trips"].sum()
    daily = daily.sort_values("trips", ascending=False)
    daily.to_csv(os.path.join(OUT_DIR, "daily_trips_2025_2026.csv"), index=False)
    top = daily.head(10)
    print("\n=== busiest days, 2025-2026 (from trip files) ===")
    print(top.to_string(index=False))

    # ---- headline metrics for the deck / README ----
    a = annual.set_index("year")
    ytd_2025 = q[(q["year"] == 2025) & (q["quarter"].str.endswith(("Q1", "Q2", "Q3")))]["trips"].sum()
    ytd_2026 = q[q["year"] == 2026]["trips"].sum()
    mtd_2025 = q[(q["year"] == 2025) & (q["quarter"].str.endswith(("Q1", "Q2", "Q3")))]["trip_minutes"].sum()
    mtd_2026 = q[q["year"] == 2026]["trip_minutes"].sum()
    lines = [
        "# Key metrics (computed by analyze.py — see outputs/*.csv)",
        "",
        f"Total trips in files: {q['trips'].sum():,} (2015Q2–2026Q3)",
        f"Total trip-minutes in files: {q['trip_minutes'].sum():,.0f}",
        "",
        "## Annual trips (full years only)",
    ]
    for y in range(2016, 2026):
        yoy = a.loc[y, "trips_yoy"]
        lines.append(
            f"- {y}: {a.loc[y, 'trips']:,.0f} trips "
            f"({yoy:+.1%} YoY)" if pd.notna(yoy) else
            f"- {y}: {a.loc[y, 'trips']:,.0f} trips")
    lines += [
        "",
        f"2019–2025 trip CAGR: {cagr(a.loc[2019, 'trips'], a.loc[2025, 'trips'], 6):+.1%}",
        f"2023–2025 trip CAGR: {cagr(a.loc[2023, 'trips'], a.loc[2025, 'trips'], 2):+.1%}",
        f"2019–2025 trip-minute CAGR: {cagr(a.loc[2019, 'trip_minutes'], a.loc[2025, 'trip_minutes'], 6):+.1%}",
        "",
        f"2026 Jan–Sep trips: {ytd_2026:,.0f} vs 2025 Jan–Sep {ytd_2025:,.0f} "
        f"({ytd_2026 / ytd_2025 - 1:+.1%})",
        f"2026 Jan–Sep trip-minutes: {mtd_2026:,.0f} vs 2025 Jan–Sep {mtd_2025:,.0f} "
        f"({mtd_2026 / mtd_2025 - 1:+.1%})",
        "",
        f"2026 Q3 trips: {q[q['quarter'] == '2026Q3']['trips'].iloc[0]:,.0f} "
        f"(YoY {q[q['quarter'] == '2026Q3']['trips_yoy'].iloc[0]:+.1%})",
        f"2026 Q2 trips: {q[q['quarter'] == '2026Q2']['trips'].iloc[0]:,.0f} "
        f"(YoY {q[q['quarter'] == '2026Q2']['trips_yoy'].iloc[0]:+.1%})",
        f"2026 Q1 trips: {q[q['quarter'] == '2026Q1']['trips'].iloc[0]:,.0f} "
        f"(YoY {q[q['quarter'] == '2026Q1']['trips_yoy'].iloc[0]:+.1%})",
        "",
        f"Stations active as of 2026-10-15: "
        f"{int((st_raw['Status'].str.lower() == 'active').sum())} "
        f"of {len(st_raw)} listed",
        f"Stations opened by end-2019: {int(stations[stations['year'] == 2019]['stations_opened_cum'].iloc[0])}",
        f"Stations opened by end-2025: {int(stations[stations['year'] == 2025]['stations_opened_cum'].iloc[0])}",
        "",
        f"Trips per station 2019: {a.loc[2019, 'trips_per_station']:,.0f}",
        f"Trips per station 2025: {a.loc[2025, 'trips_per_station']:,.0f}",
        "",
        f"Casual share of trips 2019: {a.loc[2019, 'casual_share']:.1%}",
        f"Casual share of trips 2025: {a.loc[2025, 'casual_share']:.1%}",
        f"E-bike share of trips 2019: {a.loc[2019, 'ebike_share']:.1%}",
        f"E-bike share of trips 2025: {a.loc[2025, 'ebike_share']:.1%}",
        f"E-bike share of trips 2026 Jan-Sep: "
        f"{q[q['year'] == 2026]['ebike_trips'].sum() / ytd_2026:.1%}",
        "",
        f"Mean trip duration 2019: {a.loc[2019, 'mean_duration_min']:.1f} min; "
        f"2025: {a.loc[2025, 'mean_duration_min']:.1f} min "
        f"({a.loc[2025, 'mean_duration_min'] / a.loc[2019, 'mean_duration_min'] - 1:+.1%})",
        f"Median trip duration 2019: {a.loc[2019, 'median_duration_min']:.0f} min; "
        f"2025: {a.loc[2025, 'median_duration_min']:.0f} min",
        "",
        "Busiest days 2025-2026 (trip files):",
    ] + [
        f"- {row['date']}: {row['trips']:,} trips" for _, row in top.iterrows()
    ] + [
        "",
        f"2026 Q2 YoY trips: {q[q['quarter'] == '2026Q2']['trips_yoy'].iloc[0]:+.1%} "
        f"(2025 Q2 itself was {q[q['quarter'] == '2025Q2']['trips_yoy'].iloc[0]:+.1%} YoY — soft base)",
    ]
    with open(os.path.join(OUT_DIR, "key_metrics.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))

    make_charts(q, annual, monthly)
    print("\nWrote outputs/*.csv, outputs/key_metrics.md, outputs/charts/*.png")


def make_charts(q, annual, monthly):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    BLUE, LIGHT, ORANGE = "#0B5FA5", "#7FB3D5", "#E67E22"

    # 1. Annual trips, 2016-2025 full years + 2026 Jan-Sep (hatched, labelled partial)
    full = annual[(annual["year"] >= 2016) & (annual["quarters"] == 4)]
    ytd = annual[annual["year"] == 2026].iloc[0]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(full["year"], full["trips"] / 1e6, color=BLUE, width=0.7)
    ax.bar([2026], [ytd["trips"] / 1e6], color=LIGHT, width=0.7, hatch="//",
           edgecolor=BLUE)
    for b, v in zip(bars, full["trips"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.03,
                f"{v / 1e6:.2f}m", ha="center", fontsize=9)
    ax.text(2026, ytd["trips"] / 1e6 + 0.03, f"{ytd['trips'] / 1e6:.2f}m*",
            ha="center", fontsize=9)
    ax.set_ylabel("Trips (millions)")
    ax.set_title("Indego annual trips — new record in 2023, 2024 and 2025\n"
                 "*2026 = Jan–Sep only (Q4 not yet published)")
    ax.set_xticks(list(full["year"]) + [2026])
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "annual_trips.png"), dpi=200)
    plt.close(fig)

    # 2. Quarterly trips with YoY, 2019Q1-2026Q3
    qq = q[q["quarter"] >= "2019Q1"].copy()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(qq["quarter"], qq["trips"] / 1000, color=BLUE, marker="o",
            ms=3, lw=1.6)
    ax.fill_between(qq["quarter"], qq["trips"] / 1000, color=BLUE, alpha=0.08)
    ax.set_ylabel("Trips per quarter (thousands)")
    ax.set_title("Quarterly trips — seasonality is large; compare like-for-like "
                 "quarters")
    ax.tick_params(axis="x", rotation=45)
    ax.set_xticks(qq["quarter"][::4])
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "quarterly_trips.png"), dpi=200)
    plt.close(fig)

    # 3. Revenue proxy: annual trip-minutes
    fig, ax = plt.subplots(figsize=(9, 4.6))
    bars = ax.bar(full["year"], full["trip_minutes"] / 1e6, color=ORANGE, width=0.7)
    ax.bar([2026], [ytd["trip_minutes"] / 1e6], color="#F5CBA7", width=0.7,
           hatch="//", edgecolor=ORANGE)
    for b, v in zip(bars, full["trip_minutes"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.4,
                f"{v / 1e6:.1f}m", ha="center", fontsize=9)
    ax.set_ylabel("Total trip-minutes (millions)")
    ax.set_title("Revenue proxy — total trip-minutes per year\n"
                 "*2026 = Jan–Sep only")
    ax.set_xticks(list(full["year"]) + [2026])
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "annual_trip_minutes.png"), dpi=200)
    plt.close(fig)

    # 4. Demand vs supply: trips per station (full years only — 2026 is 9 months)
    sup = annual[(annual["year"] >= 2016) & (annual["quarters"] == 4)].copy()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(sup["year"], sup["trips_per_station"], color=BLUE, marker="o", lw=2,
            label="Trips per station per year")
    ax.set_ylabel("Trips per station")
    ax.set_title("Supply grew faster than demand after 2021 — trips per station\n"
                 "fell ~20% from 2019 to 2025")
    ax2 = ax.twinx()
    ax2.plot(sup["year"], sup["stations_opened_cum"], color=ORANGE, marker="s",
             lw=1.6, label="Stations opened (cumulative)")
    ax2.set_ylabel("Stations opened (cumulative)")
    ax.set_xticks(sup["year"])
    fig.tight_layout()
    fig.subplots_adjust(right=0.85)
    fig.savefig(os.path.join(CHART_DIR, "trips_per_station.png"), dpi=200)
    plt.close(fig)

    # 5. Monthly seasonality (average trips by calendar month, 2022-2025)
    m = monthly[(monthly["month"].dt.year >= 2022) &
                (monthly["month"].dt.year <= 2025)].copy()
    m["cal_month"] = m["month"].dt.month
    seas = m.groupby("cal_month")["trips"].mean()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(seas.index, seas.values / 1000, color=BLUE, width=0.7)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                        "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Avg trips per month (thousands)")
    ax.set_title("Seasonality — average month, 2022–2025 (Jul peak ≈ 2.6× Jan)")
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "seasonality.png"), dpi=200)
    plt.close(fig)

    # 6. Passholder mix + e-bike share by year
    mix = annual[annual["year"] >= 2019].copy()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(mix["year"], mix["casual_share"] * 100, color=ORANGE, marker="o",
            lw=2, label="Casual share of trips (%)")
    ax.plot(mix["year"], mix["ebike_share"] * 100, color=BLUE, marker="s",
            lw=2, label="E-bike share of trips (%)")
    ax.set_ylabel("Share of trips (%)")
    ax.set_title("Mix shift — e-bikes keep gaining; casual share is the "
                 "event-driven swing factor")
    ax.legend(frameon=False)
    ax.set_xticks(mix["year"])
    fig.tight_layout()
    fig.savefig(os.path.join(CHART_DIR, "mix_shift.png"), dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
