"""
generate_charts.py
Produces all business-insight charts from data/data.csv → charts/

Charts produced
───────────────
1.  catalogue_size.png          — listing volume per platform
2.  median_price_retail.png     — median price positioning, retail stores
3.  price_segments.png          — price-tier mix per platform (stacked bar)
4.  discount_depth.png          — average & max discount depth per platform
5.  installment_coverage.png    — % of catalogue with financing options
6.  tap_vs_retail_prices.png    — secondary-market vs retail price buckets
7.  samsung_tab_a9_range.png    — Samsung Tab A9 price range across platforms
8.  installment_terms.png       — most popular installment terms (birmarket)
"""

import csv
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_FILE  = BASE_DIR / "data" / "data.csv"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# ── style ─────────────────────────────────────────────────────────────────────
BRAND_BLUE   = "#1a4f8a"
ACCENT_RED   = "#d94f3d"
ACCENT_GREEN = "#2e7d32"
ACCENT_GOLD  = "#e69b1e"
GREY_LIGHT   = "#f0f2f5"
GREY_MID     = "#b0b8c4"
TEXT_DARK    = "#1a1a2e"

PALETTE = [
    "#1a4f8a", "#2e7d32", "#d94f3d", "#e69b1e",
    "#5b4ea8", "#00838f", "#c2185b", "#558b2f",
    "#4527a0", "#00695c", "#ad1457",
]

def style_axes(ax, title: str, xlabel: str = "", ylabel: str = "") -> None:
    ax.set_title(title, fontsize=14, fontweight="bold", color=TEXT_DARK, pad=14)
    ax.set_xlabel(xlabel, fontsize=10, color=TEXT_DARK)
    ax.set_ylabel(ylabel, fontsize=10, color=TEXT_DARK)
    ax.tick_params(colors=TEXT_DARK, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GREY_MID)
    ax.spines["bottom"].set_color(GREY_MID)
    ax.set_facecolor(GREY_LIGHT)
    ax.grid(axis="y", color="white", linewidth=0.8)

def save(fig: plt.Figure, name: str) -> None:
    path = CHARTS_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {path.name}")


# ── load data ─────────────────────────────────────────────────────────────────
def load() -> list[dict]:
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def valid_price(row: dict) -> float | None:
    try:
        p = float(row["price_current"])
        return p if p > 1.0 else None
    except (ValueError, TypeError):
        return None


RETAIL_SOURCES = [
    "bakuelectronics.az", "bytelecom.az", "irshad.az", "kontakt.az",
    "mgstore.az", "smartelectronics.az", "soliton.az", "texnohome.az", "w-t.az",
]
MARKETPLACE_SOURCES = ["birmarket.az", "tap.az"]
ALL_SOURCES = RETAIL_SOURCES + MARKETPLACE_SOURCES

SOURCE_LABELS = {
    "bakuelectronics.az": "bakuelectronics",
    "birmarket.az":       "birmarket",
    "bytelecom.az":       "bytelecom",
    "irshad.az":          "irshad",
    "kontakt.az":         "kontakt",
    "mgstore.az":         "mgstore",
    "smartelectronics.az":"smartelectronics",
    "soliton.az":         "soliton",
    "tap.az":             "tap.az",
    "texnohome.az":       "texnohome",
    "w-t.az":             "w-t.az",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Catalogue Size by Platform
# ═══════════════════════════════════════════════════════════════════════════════
def chart_catalogue_size(rows: list[dict]) -> None:
    from collections import Counter
    counts = Counter(r["source"] for r in rows)
    items  = sorted(counts.items(), key=lambda x: x[1])

    labels = [SOURCE_LABELS.get(s, s) for s, _ in items]
    values = [v for _, v in items]
    colors = [ACCENT_RED if s in MARKETPLACE_SOURCES else BRAND_BLUE
              for s, _ in items]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(labels, values, color=colors, edgecolor="white", height=0.6)
    style_axes(ax, "Product Catalogue Size by Platform",
               ylabel="Platform", xlabel="Number of Listings")

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 12, bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va="center", ha="left", fontsize=9, color=TEXT_DARK)

    ax.set_xlim(0, max(values) * 1.15)
    patches = [
        mpatches.Patch(color=BRAND_BLUE, label="Retail Store"),
        mpatches.Patch(color=ACCENT_RED, label="Marketplace"),
    ]
    ax.legend(handles=patches, loc="lower right", framealpha=0.9, fontsize=9)
    fig.tight_layout()
    save(fig, "catalogue_size.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Median Price by Retail Store
# ═══════════════════════════════════════════════════════════════════════════════
def chart_median_price_retail(rows: list[dict]) -> None:
    prices_by_src: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r["source"] not in RETAIL_SOURCES:
            continue
        p = valid_price(r)
        if p:
            prices_by_src[r["source"]].append(p)

    items = sorted(
        [(s, statistics.median(ps)) for s, ps in prices_by_src.items()],
        key=lambda x: x[1],
    )
    labels = [SOURCE_LABELS[s] for s, _ in items]
    medians = [m for _, m in items]
    overall_med = statistics.median(
        [p for ps in prices_by_src.values() for p in ps]
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(labels, medians, color=BRAND_BLUE, edgecolor="white", width=0.6)
    ax.axhline(overall_med, color=ACCENT_RED, linewidth=1.5,
               linestyle="--", label=f"Avg Median: {overall_med:.0f} AZN")

    for bar, val in zip(bars, medians):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                f"{val:.0f}", ha="center", va="bottom", fontsize=9, color=TEXT_DARK)

    style_axes(ax, "Median Tablet Price by Retail Store",
               ylabel="Median Price (AZN)", xlabel="")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(medians) * 1.2)
    fig.tight_layout()
    save(fig, "median_price_retail.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Price Segment Mix (stacked bar)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_price_segments(rows: list[dict]) -> None:
    TIERS = [
        ("Under 300 AZN",    0,    300,  "#5c94d4"),
        ("300 – 600 AZN",   300,   600,  BRAND_BLUE),
        ("600 – 1 200 AZN", 600,  1200,  ACCENT_GOLD),
        ("Over 1 200 AZN", 1200, 99999, ACCENT_RED),
    ]

    sources = [s for s in RETAIL_SOURCES + ["birmarket.az"]
               if s in set(r["source"] for r in rows)]
    label_map = SOURCE_LABELS

    tier_data: dict[str, list[float]] = {t[0]: [] for t in TIERS}

    for src in sources:
        src_rows = [r for r in rows if r["source"] == src]
        total    = sum(1 for r in src_rows if valid_price(r))
        if not total:
            for t in TIERS:
                tier_data[t[0]].append(0)
            continue
        for tier, lo, hi, _ in TIERS:
            count = sum(
                1 for r in src_rows
                if valid_price(r) and lo <= valid_price(r) < hi
            )
            tier_data[tier].append(100 * count / total)

    x       = np.arange(len(sources))
    width   = 0.55
    bottoms = np.zeros(len(sources))
    labels  = [label_map.get(s, s) for s in sources]

    fig, ax = plt.subplots(figsize=(12, 6))
    for tier, lo, hi, color in TIERS:
        vals = tier_data[tier]
        ax.bar(x, vals, width, bottom=bottoms, label=tier, color=color,
               edgecolor="white")
        bottoms += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    style_axes(ax, "Price Segment Distribution by Platform",
               ylabel="Share of Catalogue (%)")
    ax.set_ylim(0, 105)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    save(fig, "price_segments.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Discount Depth
# ═══════════════════════════════════════════════════════════════════════════════
def chart_discount_depth(rows: list[dict]) -> None:
    def extract_pct(s: str) -> float | None:
        m = re.search(r"[\d.]+", s.strip())
        return float(m.group()) if m else None

    avg_data, max_data, src_labels = [], [], []

    for src in sorted(set(r["source"] for r in rows)):
        discs = [
            extract_pct(r["discount_pct"])
            for r in rows
            if r["source"] == src and r.get("discount_pct", "").strip()
            and extract_pct(r["discount_pct"]) is not None
        ]
        if not discs:
            continue
        src_labels.append(SOURCE_LABELS.get(src, src))
        avg_data.append(statistics.mean(discs))
        max_data.append(max(discs))

    x     = np.arange(len(src_labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width / 2, avg_data, width, label="Average Discount",
                   color=BRAND_BLUE, edgecolor="white")
    bars2 = ax.bar(x + width / 2, max_data, width, label="Maximum Discount",
                   color=ACCENT_RED, edgecolor="white")

    for bar, val in zip(bars1, avg_data):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.0f}%", ha="center", va="bottom", fontsize=9)
    for bar, val in zip(bars2, max_data):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.0f}%", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(src_labels, fontsize=10)
    style_axes(ax, "Discount Depth by Platform",
               ylabel="Discount (%)")
    ax.set_ylim(0, max(max_data) * 1.2)
    ax.legend(fontsize=9)
    fig.tight_layout()
    save(fig, "discount_depth.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Installment Financing Coverage
# ═══════════════════════════════════════════════════════════════════════════════
def chart_installment_coverage(rows: list[dict]) -> None:
    INST_COLS = ["installment_6m", "installment_12m", "installment_18m",
                 "installment_monthly", "installment", "installment_active_price"]

    results, src_labels = [], []
    for src in RETAIL_SOURCES:
        src_rows = [r for r in rows if r["source"] == src]
        if not src_rows:
            continue
        has_inst = sum(
            1 for r in src_rows
            if any(r.get(c, "").strip() for c in INST_COLS)
        )
        pct = 100 * has_inst / len(src_rows)
        results.append(pct)
        src_labels.append(SOURCE_LABELS[src])

    # sort by coverage
    paired = sorted(zip(results, src_labels), key=lambda x: x[0])
    results_s = [p[0] for p in paired]
    labels_s  = [p[1] for p in paired]

    colors = [ACCENT_GREEN if p == 100 else BRAND_BLUE if p > 50 else ACCENT_RED
              for p in results_s]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(labels_s, results_s, color=colors, edgecolor="white", height=0.55)
    ax.axvline(100, color=GREY_MID, linewidth=1, linestyle="--")

    for bar, val in zip(bars, results_s):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}%", va="center", fontsize=9)

    ax.set_xlim(0, 115)
    style_axes(ax, "Installment Financing Coverage by Retail Store",
               xlabel="% of Products with Financing Options")
    fig.tight_layout()
    save(fig, "installment_coverage.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Secondary Market vs Retail Price Distribution
# ═══════════════════════════════════════════════════════════════════════════════
def chart_tap_vs_retail(rows: list[dict]) -> None:
    BUCKETS = [
        ("< 200",   0,   200),
        ("200–400", 200, 400),
        ("400–700", 400, 700),
        ("700–1200",700, 1200),
        ("> 1200", 1200, 99999),
    ]

    def bucket_pcts(price_list: list[float]) -> list[float]:
        total = len(price_list)
        if not total:
            return [0] * len(BUCKETS)
        return [
            100 * sum(1 for p in price_list if lo <= p < hi) / total
            for _, lo, hi in BUCKETS
        ]

    tap_prices  = [p for r in rows if r["source"] == "tap.az"
                   if (p := valid_price(r))]
    retail_prices = [p for r in rows
                     if r["source"] in RETAIL_SOURCES
                     if (p := valid_price(r))]

    tap_pcts    = bucket_pcts(tap_prices)
    retail_pcts = bucket_pcts(retail_prices)

    x      = np.arange(len(BUCKETS))
    width  = 0.38
    labels = [b[0] for b in BUCKETS]

    fig, ax = plt.subplots(figsize=(11, 5))
    b1 = ax.bar(x - width / 2, retail_pcts, width, label="Retail Stores",
                color=BRAND_BLUE, edgecolor="white")
    b2 = ax.bar(x + width / 2, tap_pcts,    width, label="tap.az (Marketplace)",
                color=ACCENT_RED, edgecolor="white")

    for bar, val in zip(list(b1) + list(b2), retail_pcts + tap_pcts):
        if val > 1:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
                    f"{val:.0f}%", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    style_axes(ax, "Secondary Market vs Retail: Price Distribution",
               ylabel="Share of Listings (%)", xlabel="Price Range (AZN)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    save(fig, "tap_vs_retail_prices.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Samsung Galaxy Tab A9 Price Range Across Platforms
# ═══════════════════════════════════════════════════════════════════════════════
def chart_samsung_tab_a9(rows: list[dict]) -> None:
    keyword = "Tab A9"
    prices_by_src: dict[str, list[float]] = defaultdict(list)

    for r in rows:
        if keyword not in r.get("name", ""):
            continue
        p = valid_price(r)
        if p and p > 50:           # exclude accessories
            prices_by_src[r["source"]].append(p)

    if not prices_by_src:
        print("  [skip] no Samsung Tab A9 data found")
        return

    items = sorted(prices_by_src.items(), key=lambda x: statistics.median(x[1]))
    labels  = [SOURCE_LABELS.get(s, s) for s, _ in items]
    medians = [statistics.median(ps) for _, ps in items]
    mins_   = [min(ps)               for _, ps in items]
    maxs_   = [max(ps)               for _, ps in items]

    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(10, 6))
    # Range bars (min → max)
    for i, (lo, hi) in enumerate(zip(mins_, maxs_)):
        ax.barh(y[i], hi - lo, left=lo, height=0.35,
                color=GREY_MID, edgecolor="white", zorder=2)
    # Median dots
    ax.scatter(medians, y, color=BRAND_BLUE, s=80, zorder=4, label="Median price")
    # Min/Max labels
    for i, (lo, med, hi) in enumerate(zip(mins_, medians, maxs_)):
        ax.text(lo - 8, y[i], f"{lo:.0f}", va="center", ha="right",
                fontsize=8, color=TEXT_DARK)
        ax.text(hi + 8, y[i], f"{hi:.0f}", va="center", ha="left",
                fontsize=8, color=TEXT_DARK)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    style_axes(ax, "Samsung Galaxy Tab A9 — Price Range by Platform (AZN)",
               xlabel="Price (AZN)")
    ax.legend(fontsize=9, loc="lower right")
    ax.set_xlim(0, max(maxs_) * 1.18)
    fig.tight_layout()
    save(fig, "samsung_tab_a9_range.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 8 — Installment Term Preference (birmarket)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_installment_terms(rows: list[dict]) -> None:
    from collections import Counter
    bm = [r for r in rows
          if r["source"] == "birmarket.az" and r.get("installment_term", "").strip()]
    term_counts = Counter(r["installment_term"] for r in bm)

    # normalise term labels
    def normalise(t: str) -> str:
        m = re.search(r"\d+", t)
        return f"{m.group()} months" if m else t

    items = sorted(
        [(normalise(t), n) for t, n in term_counts.items()],
        key=lambda x: x[1], reverse=True,
    )[:8]
    labels = [i[0] for i in items]
    counts = [i[1] for i in items]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, counts, color=BRAND_BLUE, edgecolor="white", width=0.55)
    for bar, val in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 4,
                str(val), ha="center", va="bottom", fontsize=9)
    style_axes(ax, "Most Popular Installment Terms — birmarket.az",
               ylabel="Number of Listings", xlabel="Installment Term")
    fig.tight_layout()
    save(fig, "installment_terms.png")


# ═══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Price Positioning: Retail vs birmarket vs tap.az
# ═══════════════════════════════════════════════════════════════════════════════
def chart_median_all_platforms(rows: list[dict]) -> None:
    """Median price for every platform (retail + marketplaces) side by side."""
    prices_by_src: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        p = valid_price(r)
        if p:
            prices_by_src[r["source"]].append(p)

    items = sorted(
        [(s, statistics.median(ps)) for s, ps in prices_by_src.items()],
        key=lambda x: x[1],
    )
    labels  = [SOURCE_LABELS.get(s, s) for s, _ in items]
    medians = [m for _, m in items]
    colors  = [ACCENT_RED if s in MARKETPLACE_SOURCES else BRAND_BLUE
               for s, _ in items]

    fig, ax = plt.subplots(figsize=(11, 5))
    bars = ax.bar(labels, medians, color=colors, edgecolor="white", width=0.6)
    for bar, val in zip(bars, medians):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10,
                f"{val:.0f}", ha="center", va="bottom", fontsize=9)
    style_axes(ax, "Median Listing Price: All Platforms Compared",
               ylabel="Median Price (AZN)")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    patches = [
        mpatches.Patch(color=BRAND_BLUE, label="Retail Store"),
        mpatches.Patch(color=ACCENT_RED, label="Marketplace"),
    ]
    ax.legend(handles=patches, fontsize=9)
    ax.set_ylim(0, max(medians) * 1.2)
    fig.tight_layout()
    save(fig, "median_all_platforms.png")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print(f"Loading {DATA_FILE} …")
    rows = load()
    print(f"  {len(rows):,} rows loaded\n")

    print("Generating charts …")
    chart_catalogue_size(rows)
    chart_median_price_retail(rows)
    chart_price_segments(rows)
    chart_discount_depth(rows)
    chart_installment_coverage(rows)
    chart_tap_vs_retail(rows)
    chart_samsung_tab_a9(rows)
    chart_installment_terms(rows)
    chart_median_all_platforms(rows)

    print(f"\nAll charts saved to {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
