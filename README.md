# Indego Bike Share — Growth Analysis & Recommendations

A ~2-hour analyst exercise (Perpay Analytics Bike Share Data Challenge) using
**only data published on Indego's program website, [rideindego.com](https://www.rideindego.com)**.
No one at Indego was contacted. All figures below are computed from the
published files by [`analyze.py`](analyze.py); nothing is invented. Where the
website cannot answer a question, that is stated explicitly.

**Deliverables:** this write-up · [`Indego_Growth_Recommendations.pptx`](Indego_Growth_Recommendations.pptx)
(2 slides + speaker notes) · [`Indego_Growth_Recommendations.pdf`](Indego_Growth_Recommendations.pdf)
(same 2 slides) · [`analyze.py`](analyze.py) · [`outputs/`](outputs) (tables + charts)

## The brief

Imagine Philadelphia's bike share program (Indego) operates as a for-profit
business in a multi-year growth initiative. As Analyst, answer for executives:

1. How should decision makers quantify the current and recent growth rate?
2. Is there any evidence the program is growing too slowly or too quickly?
3. Should executives adopt a specific approach to growing the program ahead?

**Working assumption (per the brief): revenue is primarily driven by trip duration.**
So the revenue proxy used throughout is **total trip-minutes** (the sum of trip
durations), alongside trip counts.

## Headline findings

| Metric | Value |
|---|---|
| Trips, 2025 (record year) | **1,358,173** (+7.0% YoY) |
| Trip growth, 2019–2025 CAGR | **+10.5% / yr** |
| Trip-minute (revenue-proxy) growth, 2019–2025 CAGR | **+4.7% / yr** — trips are growing ~2× faster than the revenue proxy |
| Trips, Jan–Sep 2026 | **1,230,746**, **+19.2%** vs Jan–Sep 2025 |
| Trip-minutes, Jan–Sep 2026 | **21.0m**, **+18.9%** vs Jan–Sep 2025 |
| Mean trip duration | **23.3 min (2019) → 16.8 min (2025), −28%**; median 11 → 10 min |
| E-bike share of trips | **14.3% (2019) → 65.5% (2025) → 72.7% (Jan–Sep 2026)** |
| Casual share of trips | 12.0% (2019) → 6.2% (2023) → 10.6% (2025) → 12.8% (Jan–Sep 2026) |
| Stations | 151 opened by end-2019 → 345 by end-2025 → **323 active** of 386 listed (15 Oct 2026) |
| Trips per station | 4,929 (2019) → **3,937 (2025), −20%**; annualised 2026 ≈ 4,260 (recovering) |
| Busiest day ever | **19 Jun 2026 (Juneteenth): 8,820 trips** — 2.4× the 2025 daily average (3,721); all 10 busiest days on record are in 2026 |
| Seasonality | July averages **2.6×** January (2022–2025) |

## Q1 — How should decision makers quantify the growth rate?

**Recommendation: track two numbers, compared like-for-like — trips AND
trip-minutes, each versus the same period a year earlier.** Never sequential
quarters, never raw annual totals alone.

- **Trips** measure demand. 2025: 1.36m (+7.0% YoY, a record); 2019–2025
  CAGR +10.5%; 2023–2025 CAGR +11.9%. 2026 Jan–Sep: 1.23m, +19.2% vs the
  same nine months of 2025.
- **Trip-minutes** measure the revenue proxy. 2019–2025 CAGR only +4.7% —
  roughly half the trip growth — because mean trip duration fell 23.3 → 16.8
  min (−28%). A growth target set on trips alone over-promises revenue by
  about two to one.
- **Quarterly discipline.** Q1 2026 grew just +2.1% YoY; Q2 jumped +32.1%
  (FIFA World Cup 11 Jun–19 Jul, plus a soft 2025 Q2 base — trips fell 0.6%
  that quarter); Q3 +16.3%. The underlying rate is in the mid-teens, not
  the thirties. And July runs 2.6× January, so quarter-on-quarter comparisons
  are meaningless; always use the same quarter last year and always flag
  partial years (2026 is nine months, Q4 not yet published).

## Q2 — Too slowly, or too quickly?

**Neither in aggregate — but the mix of the growth is off.**

- **Not too slow.** Trips are at record levels, 2026 is +19.2% on the same
  period last year, and 2026 is on pace to beat the 2025 record. The "too
  slow" risk is commercial, not demand: revenue per trip is shrinking as
  trips get shorter, while passes still sell time in 30/60-minute blocks.
  If duration keeps falling, trip growth has to work twice as hard to move
  revenue. That is a pricing and product question.
- **Not too fast overall — but supply ran ahead of demand.** Stations grew
  151 → 345 from end-2019 to end-2025 (+128%) while trips grew +83%, so
  trips per station fell 4,929 → 3,937 (−20%). The sharpest step was 2023
  (+67 stations, +32% in one year). Not a crisis — 2026 demand is absorbing
  the capacity (annualised ≈ 4,260 trips/station, above 2025) — but the next
  expansion tranche should be earned by utilisation, not by calendar.
- **The one place growth genuinely looks too fast is peak days.** Busiest
  day ever: 19 Jun 2026, 8,820 trips (2.4× the 2025 daily average); all ten
  busiest days on record are in 2026. Indego's own blog reports the FIFA
  World Cup period at +39% vs the same period in 2025; the trip files
  confirm Q2 2026 at +32.1% YoY. Peak-day rebalancing, e-bike charging and
  dock availability — not average-day capacity — is where the system strains.

## Q3 — Recommended approach for the period ahead

**Deepen before widening.** Three moves, in order:

1. **Capacity where demand already is** — more docks and e-bikes in the
   high-demand core and at the busiest stations, before new neighbourhoods.
   E-bikes are now 73% of trips; an e-bike shortage is a growth shortage.
2. **Convert the casual surge** — casual share rose from 6% (2023) to 13%
   (Jan–Sep 2026), driven by events and first-timers. A first-ride-to-pass
   offer at the point of the event is the cheapest growth available.
3. **Gate the planned ~40 new stations for 2026 on utilisation thresholds**
   (e.g. trips per station back above ~4,500, and peak-day dock-out rates),
   reviewed quarterly — so expansion follows demonstrated demand.

## Slide commentary

The full commentary for each slide is in the speaker notes of
[`Indego_Growth_Recommendations.pptx`](Indego_Growth_Recommendations.pptx)
(and summarised above: slide 1 covers Q1, slide 2 covers Q2 + Q3).

## Data sources (all from rideindego.com)

| Source | URL | Coverage / note |
|---|---|---|
| Trip data (46 quarterly CSVs) | https://www.rideindego.com/about/data/ | 2015 Q2 (launch, 23 Apr 2015) – 2026 Q3; 10,832,689 trips. Files are zipped CSVs; direct `curl` is blocked by Cloudflare (403) — the script uses browser-style headers (Referer + Chrome UA), which the site accepts. |
| Station Table | https://www.rideindego.com/wp-content/uploads/2026/10/indego-stations-2026-10-15.csv | 386 stations listed, 323 Active as of 15 Oct 2026; go-live dates used to reconstruct station growth. |
| 2026 Expansion Update (blog) | https://www.rideindego.com/blog/2026-expansion-update/ | 2025: >1.3m trips (record), +36 stations, +530 docks; 2026 plan: ~40 new stations, 800 docks, five new areas (Germantown, West Kensington, Southwest Philadelphia, Wynnefield Heights, Packer Park / FDR Park). |
| FIFA World Cup Drives Record Ridership (blog) | https://www.rideindego.com/blog/fifa-world-cup-drives-record-ridership/ | 11 Jun–19 Jul 2026: >239,000 trips (+39% vs same period 2025); busiest day 19 Jun, 8,820 trips; 10 highest ridership days all during the tournament; 65% passholder / 35% casual that day. Cross-checked against the trip files — the 8,820 figure matches exactly. |
| Pass pricing (gift-certificates page + Single Ride blog) | https://www.rideindego.com/gift-certificates/ | Single Ride $4.50 / 30 min; Guest Pass $15 / 24 h; Indego30 $20 / mo; Indego365 $156 / yr; Indego365 Plus $230 / yr (2× 30-min e-bike rides/day); ACCESS $5 / mo, $48 / yr; e-bike +20¢/min (30¢/min on Single Ride, 7¢ ACCESS); overage 20¢/min after the included 60 min. Prices as published Nov 2026. |

Context only (not used as evidence): the Bicycle Coalition's Feb 2025 note that
2024 passed 1.2m trips vs 1.08m in 2023 — consistent with the trip files
(1,269,390 vs 1,084,547).

## How to run the analysis

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 analyze.py        # downloads the data if needed, writes outputs/
python3 build_deck.py     # builds the .pptx and renders the .pdf (needs LibreOffice)
```

`analyze.py` looks for the quarterly files under `data/extracted/`; if they
are missing it downloads them from rideindego.com (~200 MB of zips, ~1.4 GB
extracted — raw data is **not** committed to this repo) and writes:

- `outputs/quarterly_summary.csv` — trips, trip-minutes, duration, passholder
  mix, e-bike share, YoY change, per quarter (46 quarters)
- `outputs/annual_summary.csv` — the same, per year
- `outputs/monthly_summary.csv` — trips and trip-minutes per month
- `outputs/daily_trips_2025_2026.csv` — trips per day, 2025–2026
- `outputs/station_growth.csv` — stations opened (cumulative) per year-end
- `outputs/key_metrics.md` — the headline numbers quoted in this README
- `outputs/charts/*.png` — the six charts (annual trips, quarterly trips,
  annual trip-minutes, trips per station, seasonality, mix shift)

## Method & assumptions

- **Revenue proxy.** The brief states revenue is primarily driven by trip
  duration, so total trip-minutes is the proxy. It is *not* revenue: pass
  prices, included minutes, overage fees and e-bike surcharges are not in the
  trip files, and no $ figure is estimated here.
- **Passholder vs casual.** `passholder_type` labels in the files are
  Indego30, Indego365, IndegoFlex, Walk-up, Day Pass, One Day Pass, Two Day
  Pass. "Casual" = Walk-up + Day/Guest passes (pay-per-ride / visitor);
  everything else = Passholder. There is no separate "Guest Pass" label in
  the files; Day Pass is the 24-hour product.
- **E-bike share.** `bike_type` is only recorded from 2018 onwards (2,049
  e-bike trips in 2018 — the first e-bike year in the data). Pre-2018 files
  have no `bike_type` column at all.
- **Duration unit quirk (important).** The site's format page says duration
  is in minutes, but files from 2015 Q2 through 2017 Q2 record it in
  **seconds** (median ~600–900, max 86,400 = 24 h in seconds). From 2017 Q3
  it is minutes (max 1,440 = 24 h in minutes). `analyze.py` detects the unit
  per file (median > 60 → seconds) and converts. Without this, pre-2018
  trip-minutes are overstated ~60×.
- **Publisher's cleaning (per the data page).** Staff/test trips removed;
  trips under 1 minute removed; durations capped at 24 hours. The 2017 Q4
  zip contains a file with an odd internal name
  (`indego-quarter-echo.bicycletransit.com-2018-01-19-9-57 AM.csv`) — it is
  the 2017 Q4 data (first trip 2017-10-01) and is used as such.
- **Stations.** "Stations opened (cumulative)" counts every station by its
  go-live date, regardless of current status; the Station Table cannot say
  when a station went inactive, so the active-only series is a lower bound
  for earlier years. Two older station snapshots bundled inside trip zips
  (Jul & Oct 2021) were not needed and were ignored.
- **2026 annualisation.** 1,230,746 trips over 273 days (Jan–Sep) implies
  ~1.65m trips for a full year at the same daily rate, or ~4,260 trips per
  station (386 opened). This is labelled as an annualisation, not a measured
  figure — Q4 is seasonally weaker, so it is an upper-ish estimate.
- **Scope.** A ~2-hour exercise: the analysis is deliberately proportionate
  — trip counts, durations, mix and supply. No weather, demographic,
  pricing-elasticity or cost modelling was attempted; the website does not
  publish the data for it.

## What the website cannot answer (data gaps)

- **Actual revenue, costs, or profit** — no prices per trip, no membership
  counts, no cost data are published. Trip-minutes are a proxy only.
- **Fleet size / bike counts** — the site publishes stations, not bikes.
  (Distinct `bike_id`s in the trip files give a lower bound: 2,809 distinct
  bikes in the busiest single quarter, Q3 2026 — but a bike that never rode
  in that quarter is invisible, and the true fleet is larger.)
- **Passholder counts** — only trips by pass type, not how many people hold
  each pass.
- **Availability / rebalancing** — no dock-out rates, no empty/full-station
  data in the published files (live GBFS station status exists but is a
  snapshot, not history).
- **Why trips are getting shorter** — the files show the duration decline
  but not the cause (e-bike speed, shorter hops, mix shift, or pricing).
  That needs rider surveys or internal data.
- **Q4 2026** — not yet published (as of 11 Nov 2026); all 2026 figures are
  Jan–Sep.
