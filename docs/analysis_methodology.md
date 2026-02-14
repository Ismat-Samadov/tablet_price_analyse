# Analysis Methodology

This document explains how each chart in `charts/` was produced, what data decisions were made, and what the known limitations of each insight are.

---

## Data Preparation

Before any chart is generated, `scripts/generate_charts.py` applies two filters to the loaded dataset:

### 1. Price validity filter

```python
def valid_price(row) -> float | None:
    p = float(row["price_current"])
    return p if p > 1.0 else None
```

Prices at or below 1.0 AZN are treated as invalid and excluded. This removes:
- `0.00` — out-of-stock products on texnohome.az that display no price
- `0.01` — a placeholder price on kontakt.az for a discontinued product

### 2. Platform classification

Platforms are split into two groups for charts that distinguish channel type:

**Retail stores** (branded, stock-holding):
`bakuelectronics.az`, `bytelecom.az`, `irshad.az`, `kontakt.az`, `mgstore.az`, `smartelectronics.az`, `soliton.az`, `texnohome.az`, `w-t.az`

**Marketplaces** (multi-seller, individual listings):
`birmarket.az`, `tap.az`

This split matters because marketplace listings include used, refurbished, and grey-import devices alongside new stock — mixing them with retail in price comparisons would distort the picture.

---

## Chart-by-Chart Explanation

---

### 1. `catalogue_size.png` — Product Catalogue Size by Platform

**What is counted:** Every row in `data.csv`, one row per listing. No price filtering is applied.

**Colour coding:** Blue = retail store, Red = marketplace.

**Limitation:** Raw listing count is not equivalent to catalogue breadth. On tap.az and birmarket.az the same physical product can appear as many separate listings from different sellers. On retail stores, each row is a distinct SKU. The chart therefore reflects *market activity volume* on marketplaces and *catalogue depth* on retail stores — two different things displayed on the same axis.

---

### 2. `median_price_retail.png` — Median Price by Retail Store

**What is calculated:** The statistical median of all valid `price_current` values for each retail store. The dashed red reference line shows the median of all retail prices pooled together.

**Why median, not average:** The price distribution in each catalogue is right-skewed (a few premium models pull the average up significantly). The median more accurately represents the typical product a buyer would encounter.

**Excluded:** birmarket.az and tap.az are not shown here because they are marketplaces, not retail stores. Their median prices are shown in the companion chart `median_all_platforms.png`.

**Limitation:** Retailers with a small catalogue (w-t.az: 8 products, texnohome: 9 valid prices) have medians that are highly sensitive to their specific product mix. A single model change can shift the median significantly.

---

### 3. `median_all_platforms.png` — Median Price: All Platforms

**What is calculated:** Same as above but includes birmarket.az and tap.az.

**Interpretation note:** The birmarket median (227 AZN) and tap.az median (424 AZN) are not directly comparable to retail medians because they represent entirely different product compositions (many budget/used models, older generations). This chart is primarily useful for showing the floor of consumer expectations — where buyers can find the cheapest devices.

---

### 4. `price_segments.png` — Price Segment Distribution by Platform

**How segments are defined:**

| Tier | Price Range | Market positioning |
|------|-------------|-------------------|
| Under 300 AZN | < 300 | Entry-level / budget |
| 300–600 AZN | 300–599 | Mainstream |
| 600–1,200 AZN | 600–1,199 | Upper-mid / prosumer |
| Over 1,200 AZN | ≥ 1,200 | Premium |

**What is calculated:** For each platform, the count of valid-price products in each tier is divided by the total valid-price count to produce a percentage share. Each bar therefore sums to 100%.

**Included platforms:** All retail stores + birmarket.az. tap.az is excluded because its listings include accessories and older-generation devices that would distort the tier distribution.

**Limitation:** The tier boundaries are chosen for this market — they may not correspond to global market conventions. The 600–1,200 AZN band, for example, would be considered mid-range globally but is "upper-mid" in the Azerbaijan context given the local income distribution.

---

### 5. `discount_depth.png` — Discount Depth by Platform

**What is calculated:**
- **Average discount:** `mean()` of all parsed `discount_pct` values per platform
- **Maximum discount:** `max()` of the same set

**Parsing:** `re.search(r"[\d.]+", discount_pct_string)` extracts the numeric value, handling formats like `"15%"`, `"-16%"`, and `"27"`.

**Platforms shown:** Only those with at least one populated `discount_pct` value: birmarket, irshad, soliton, texnohome.

**Why most retailers have no discount data:**
bakuelectronics, bytelecom, kontakt, mgstore, smartelectronics, and w-t.az do not display a discount percentage on their listing pages (even when `price_old` is present). They are omitted from this chart — not because they don't discount, but because the discount percentage is not scraped from their pages.

**Limitation:** The absence of a discount percentage on a listing page does not mean no discount exists. Retailers that show `price_old` without a percentage (e.g. kontakt, mgstore) are discounting silently — buyers must compute the percentage themselves. This chart may understate the true level of discounting in the market.

---

### 6. `installment_coverage.png` — Installment Financing Coverage

**What is calculated:** For each retail store, the percentage of products that have at least one populated installment column (`installment_6m`, `installment_12m`, `installment_18m`, `installment_monthly`, `installment`, or `installment_active_price`).

**Colour coding:**
- Green = 100% coverage (all products have financing)
- Blue = > 50% coverage
- Red = < 50% coverage

**Excluded:** birmarket.az and tap.az are not shown (birmarket has installment data but is a marketplace, not a retail store; tap.az has no financing data).

**Limitation:** The presence of installment data in the scraped output means the financing option was displayed on the listing card. Some retailers may offer financing only at the checkout stage, which would not be captured here.

---

### 7. `tap_vs_retail_prices.png` — Secondary Market vs Retail Price Distribution

**What is calculated:** For both tap.az and the pooled set of all retail stores, the count of valid-price products in each price bucket is divided by the respective total to give percentage shares:

| Bucket | Range |
|--------|-------|
| < 200 AZN | 0–199 |
| 200–400 AZN | 200–399 |
| 400–700 AZN | 400–699 |
| 700–1,200 AZN | 700–1,199 |
| > 1,200 AZN | ≥ 1,200 |

**Limitation:** tap.az listings include accessories, cases, keyboards, and chargers that are not tablets. These lower-priced items inflate the `< 200 AZN` bucket for tap.az. A stricter analysis would filter by listing title for device-only content, but this is not applied in the current pipeline. The practical effect is that the secondary-market share below 200 AZN is likely slightly overstated.

---

### 8. `samsung_tab_a9_range.png` — Samsung Tab A9 Price Range

**How products are selected:** `"Tab A9"` is searched as a substring in the `name` column (case-sensitive). Prices ≤ 50 AZN are excluded to filter out accessories (cases, screen protectors) whose listings contain "Tab A9" in the title.

**What is displayed:**
- Grey horizontal bar = price range (minimum to maximum) per platform
- Blue dot = median price per platform
- Labels at each end show minimum and maximum values

**Limitation:**
- The search string `"Tab A9"` matches both the Tab A9 (base) and Tab A9+ (Plus) models. These have different hardware and price points. A product-level analysis would require exact model matching by SKU.
- tap.az listings include some accessories (e.g. `"Samsung Galaxy Tab A9" case`) at very low prices. The 50 AZN floor filters most of these but may not catch all of them.
- The sample sizes vary significantly: tap.az has ~80 listings for this model, while w-t.az has one. Single-product platforms show a range of zero width.

---

### 9. `installment_terms.png` — Most Popular Installment Terms

**Data source:** birmarket.az rows where `installment_term` is populated.

**Why birmarket:** It is the only source with enough listings (582) and term variety to make a term-distribution chart statistically meaningful. Other sources with term data (bakuelectronics: 55 rows, smartelectronics: 80 rows) have too little variation.

**Normalisation:** Term values like `"18 ay"` are parsed to `"18 months"` for display clarity.

**Limitation:** birmarket's installment terms reflect its platform-level consumer finance partner, not individual seller choices. The distribution shows which terms the platform makes available and which buyers/sellers most commonly select — it is not a representative sample of the entire Azerbaijan market.

---

## Known Data Limitations

### Cross-source comparability

No standardised product taxonomy exists across the sources. A "Samsung Galaxy Tab A9 4/64GB" may be listed under different names, spellings, and configurations across platforms. Cross-source comparison (as in the Samsung Tab A9 chart) requires loose text matching that may include near-variants or exclude exact matches.

### Snapshot data

All data was collected in a single scraping session in February 2026. Prices, stock levels, and discounts change daily. The analysis reflects a point-in-time snapshot, not a time series.

### Marketplace vs retail mixing

birmarket.az and tap.az list both new and used devices. Where these are included in analysis alongside retail stores (e.g. the price segment chart includes birmarket), the interpretation must account for the fact that used-device pricing and new-retail pricing are fundamentally different signals.

### Missing in-stock data

Most retail stores (bakuelectronics, birmarket, bytelecom, irshad, kontakt, mgstore, w-t.az) do not expose stock status on their listing pages, or the scrapers do not capture it. For these sources, `in_stock` is empty in `data.csv`. The true in-stock rate across the market is therefore unknown.

### soliton.az: all out-of-stock

The soliton.az scraper marks all 53 products as `in_stock = "False"`. This correctly reflects the `.outofstock` class present on every product card at the time of collection — the entire tablet catalogue was out of stock on that date.

### texnohome.az: sparse price data

12 of 21 texnohome.az products were out of stock, showing `price_current = "0.00"`. Only 9 products have valid prices. This platform's contribution to price analysis is limited.
