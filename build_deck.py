#!/usr/bin/env python3
"""
Build the 2-slide executive deck for the Indego bike-share growth analysis.

Reads the charts produced by analyze.py (outputs/charts/*.png) and the
numbers in outputs/key_metrics.md, and writes:
  - Indego_Growth_Recommendations.pptx  (2 slides + speaker notes)
  - Indego_Growth_Recommendations.pdf   (rendered via LibreOffice, same 2 slides)

All figures are taken from the trip files published on rideindego.com
(see README.md). No figure is invented.
"""

import os
import subprocess

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

BASE = os.path.dirname(os.path.abspath(__file__))
CHARTS = os.path.join(BASE, "outputs", "charts")
PPTX_PATH = os.path.join(BASE, "Indego_Growth_Recommendations.pptx")
PDF_PATH = os.path.join(BASE, "Indego_Growth_Recommendations.pdf")

BLUE = RGBColor(0x0B, 0x5F, 0xA5)
DARK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x5A, 0x5A, 0x5A)
LIGHT_BG = RGBColor(0xF2, 0xF6, 0xFA)
ACCENT = RGBColor(0xE6, 0x7E, 0x22)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_text(slide, x, y, w, h, text, size=14, bold=False, color=DARK,
             alignment=None):
    from pptx.enum.text import PP_ALIGN
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    if alignment is not None:
        p.alignment = alignment
    return box


def add_bullets(slide, x, y, w, h, items, size=13, gap=6):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, (text, bold) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = DARK
        p.space_after = Pt(gap)
        p.level = 0
    return box


def header(slide, kicker, title):
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333),
                                 Inches(1.05))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    add_text(slide, 0.5, 0.12, 12.3, 0.3, kicker, size=11, bold=True,
             color=RGBColor(0xBF, 0xDB, 0xF0))
    add_text(slide, 0.5, 0.38, 12.3, 0.6, title, size=24, bold=True,
             color=RGBColor(0xFF, 0xFF, 0xFF))


def footer(slide, text):
    add_text(slide, 0.5, 7.08, 12.33, 0.3, text, size=9, color=GREY)


def rec_box(slide, y, text):
    box = slide.shapes.add_shape(1, Inches(0.5), Inches(y), Inches(12.33),
                                 Inches(0.72))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT_BG
    box.line.color.rgb = BLUE
    box.line.width = Pt(1.25)
    add_text(slide, 0.75, y + 0.08, 11.9, 0.6,
             "RECOMMENDATION  —  " + text, size=13, bold=True, color=BLUE)


def notes(slide, text):
    slide.notes_slide.placeholders[1].text = text


# ---------------------------------------------------------------- slide 1
s1 = prs.slides.add_slide(BLANK)
header(s1, "INDEGO BIKE SHARE  •  GROWTH REVIEW  •  SLIDE 1 OF 2",
       "Growth is real — and it is accelerating again in 2026")
s1.shapes.add_picture(os.path.join(CHARTS, "annual_trips.png"),
                      Inches(0.5), Inches(1.35), width=Inches(7.6))
add_bullets(s1, 8.4, 1.45, 4.45, 4.4, [
    ("1.36m trips in 2025 — a record year (+7.0% YoY).", True),
    ("Trips grew +10.5% a year, 2019–2025 (CAGR).", False),
    ("2026 Jan–Sep: 1.23m trips, +19.2% vs the same months of 2025.", True),
    ("But the revenue proxy lags: trip-minutes grew only +4.7% a year, "
     "2019–2025 — mean trip length fell 23.3 → 16.8 min (−28%).", False),
    ("Q1 2026 was soft (+2.1% YoY); Q2 (+32.1%) was flattered by the "
     "FIFA World Cup and a weak 2025 Q2 base.", False),
    ("July runs ~2.6× January — never compare sequential quarters.", False),
], size=13.5)
rec_box(s1, 6.15,
        "Measure growth as like-for-like YoY change in trips AND trip-minutes "
        "(the revenue proxy) — not raw totals, not quarter-on-quarter.")
footer(s1, "Source: Indego quarterly trip files, rideindego.com/about/data (2015 Q2–2026 Q3, "
           "10.83m trips). 2026 = Jan–Sep only. Trip-minutes = sum of trip durations; "
           "revenue is assumed to be driven by trip duration, per the brief.")
notes(s1, """SLIDE 1 — COMMENTARY (for the manager, then the executive team)

Q1: How should decision makers quantify the current and recent growth rate?

The honest answer is: with two numbers, compared like-for-like — trips and
trip-minutes, each versus the same period a year earlier. Trips alone flatter
the story; minutes alone hide it. Together they show what is really
happening.

Trips: 2025 was a record year at 1.36 million trips (+7.0% year on year),
and the 2019–2025 compound growth rate is +10.5% a year. 2026 is running
hot: 1.23 million trips in January–September, +19.2% against the same nine
months of 2025 — already more than the whole of 2023. The quarterly split
matters, though: Q1 2026 grew only +2.1%, while Q2 jumped +32.1%. Q2 had
two tailwinds — the FIFA World Cup (11 June–19 July) and a soft 2025 Q2
base (trips actually fell 0.6% that quarter). Strip the event out and the
underlying rate is closer to the mid-teens than the thirties.

Trip-minutes — our revenue proxy, since the brief says revenue is driven
primarily by trip duration — grew much more slowly: +4.7% a year from 2019
to 2025, against +10.5% for trips. The reason is duration: the mean trip
shortened from 23.3 minutes in 2019 to 16.8 minutes in 2025 (−28%), while
the median barely moved (11 → 10 minutes). More, shorter trips. That is
consistent with the e-bike shift (next slide) and with more short
centre-city hops — but it means trip-count growth overstates revenue
growth by roughly two to one. Any growth target set on trips alone will
over-promise revenue.

Seasonality is the trap to avoid: July averages 2.6× January (2022–2025),
so sequential quarters are meaningless. Always use the same quarter last
year, and always show the partial-year flag — 2026 is nine months, not
twelve.

Data note: every figure here is computed from the 46 quarterly trip files
published on rideindego.com (10.83 million trips, April 2015–September
2026). One wrinkle worth knowing: files from 2015 Q2 to 2017 Q2 record
duration in seconds, not minutes as the site's format page states — the
analysis detects and converts this per file.""")

# ---------------------------------------------------------------- slide 2
s2 = prs.slides.add_slide(BLANK)
header(s2, "INDEGO BIKE SHARE  •  GROWTH REVIEW  •  SLIDE 2 OF 2",
       "Grow by deepening the core — capacity and conversion first")
s2.shapes.add_picture(os.path.join(CHARTS, "trips_per_station.png"),
                      Inches(0.5), Inches(1.35), width=Inches(7.6))
add_bullets(s2, 8.4, 1.45, 4.45, 4.4, [
    ("Supply ran ahead of demand: stations 151 → 345 (end-2019 → end-2025, "
     "+128%); trips per station fell 4,929 → 3,937 (−20%).", True),
    ("E-bikes are the growth engine: 14% of trips in 2019 → 66% in 2025 → "
     "73% in Jan–Sep 2026.", False),
    ("Casual riders are back: 6% of trips in 2023 → 11% in 2025 → 13% in "
     "2026 — events convert first-timers, if we catch them.", False),
    ("Peak-day strain is real: 8,820 trips on 19 Jun 2026 (Juneteenth) — "
     "2.4× the 2025 daily average (3,721); the 10 busiest days ever are all "
     "in 2026.", False),
    ("2026 demand (+19.2% Jan–Sep) is now absorbing the 2023–25 capacity "
     "build — utilisation is recovering, not collapsing.", False),
], size=13.5)
rec_box(s2, 6.15,
        "Deepen before widening: add docks and e-bikes in high-demand core zones, "
        "convert casual/event riders to passes, and gate new stations on utilisation.")
footer(s2, "Source: Indego quarterly trip files + Station Table (323 active stations, 15 Oct 2026), "
           "rideindego.com. 2026 expansion plan (~40 stations) per Indego's 2026 Expansion Update blog post.")
notes(s2, """SLIDE 2 — COMMENTARY (for the manager, then the executive team)

Q2: Is there evidence the program is growing too slowly or too quickly?

Neither, in aggregate — but the mix of the growth is off. On "too slowly":
no. Trips are at record levels, 2026 is +19.2% on the same period last
year, and 2026 is on pace to beat the 2025 record (1.23m trips in nine
months, against 1.36m for the whole of 2025). The "too slow" risk is narrower and commercial: revenue per trip is
shrinking, because trips are getting shorter (−28% mean duration since
2019) while the pass structure still sells time in 30/60-minute blocks.
If duration keeps falling, trip growth has to work twice as hard to move
revenue. That is a pricing and product question, not a demand problem.

On "too quickly": the evidence is in the supply line. Stations grew from
151 at end-2019 to 345 at end-2025 (+128%), while trips grew +83% over the
same span — so trips per station fell from 4,929 to 3,937 (−20%). The 2023
expansion was the sharpest single step (+67 stations, +32% in one year).
That is not a crisis — 2026 demand is absorbing the capacity (annualising
the nine months of 2026 implies ~1.65m trips for a full year, or ~4,260
per station, above 2025's 3,937), and new stations in Richmond, Roxborough
and Wynnefield were an equity choice, not purely a commercial one — but it
does mean the next expansion tranche should be earned by utilisation, not
by calendar.

The one place growth genuinely looks "too fast" is peak days. The busiest
day ever was 19 June 2026 (Juneteenth): 8,820 trips, 2.4× the 2025 daily
average of 3,721 trips, and all ten of the busiest days on record fall in
2026. The FIFA World Cup
period (11 June–19 July) ran +39% on the same period in 2025, per Indego's
own blog, and our trip files confirm Q2 2026 at +32.1% YoY. Peak-day
rebalancing, e-bike charging and dock availability — not average-day
capacity — is where the system strains.

Q3: What approach should executives adopt for the period ahead?

Deepen before widening. Three moves, in order:
1. Capacity where demand already is — more docks and e-bikes in the
   high-demand core and at the busiest stations, before new neighbourhoods.
   E-bikes are now 73% of trips; an e-bike shortage is a growth shortage.
2. Convert the casual surge — casual share rose from 6% (2023) to 13%
   (2026 Jan–Sep), driven by events and first-timers. A first-ride-to-pass
   offer at the point of the event is the cheapest growth available.
3. Gate the planned ~40 new stations for 2026 on utilisation thresholds
   (e.g. trips per station back above ~4,500, and peak-day dock-out rates),
   and review quarterly — so expansion follows demonstrated demand.

What we cannot answer from the program website: actual revenue, costs,
passholder counts, fleet size, dock-out/rebalancing data, or why trips are
getting shorter. Those need internal data. The trip files tell us volume
and duration; they do not tell us money.""")

prs.save(PPTX_PATH)
print(f"Saved {PPTX_PATH}")

# Render a PDF with LibreOffice (headless) so the slides are verifiable.
subprocess.run(
    ["soffice", "--headless", "--convert-to", "pdf", "--outdir", BASE,
     PPTX_PATH],
    check=True, capture_output=True, text=True,
)
print(f"Saved {PDF_PATH}")
