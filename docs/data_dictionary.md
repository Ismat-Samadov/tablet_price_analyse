# Data Dictionary

This document defines every field in every CSV produced by this project.

---

## 1. Master Dataset — `data/data.csv`

The combined, normalised dataset. **3,559 rows × 33 columns.**

Every row has a `source` column identifying which platform it came from. Source-specific columns are present for all rows but empty for rows from platforms that do not provide that data.

| Column | Type | Description | Sources that populate it |
|--------|------|-------------|--------------------------|
| `source` | string | Domain name of the originating platform (e.g. `kontakt.az`, `tap.az`) | All |
| `name` | string | Product display name / listing title | All |
| `product_id` | string | Platform-specific product identifier (may be numeric ID, SKU code, or legacy resource ID) | All except kontakt.az (uses `sku`) |
| `sku` | string | Stock-keeping unit code | bakuelectronics, kontakt, mgstore |
| `brand` | string | Brand name | kontakt, mgstore, soliton (via brand_id) |
| `category` | string | Product category label as shown on the platform | irshad (product_type), kontakt, mgstore, soliton, smartelectronics |
| `price_current` | decimal string | Current selling price in AZN. For discounted items this is the sale price. May be `"0.00"` for out-of-stock items on texnohome.az | All |
| `price_old` | decimal string | Original price before discount, in AZN. Empty if no discount is shown | Most retail sources |
| `discount_pct` | string | Discount percentage shown on the listing, e.g. `"15%"` or `"-16%"` | birmarket, irshad, kontakt, soliton, texnohome |
| `discount_amount` | decimal string | Absolute discount value in AZN | bakuelectronics, irshad, kontakt, mgstore, soliton |
| `installment_6m` | decimal string | Monthly payment under a 6-month financing plan, in AZN | irshad, soliton, w-t.az |
| `installment_12m` | decimal string | Monthly payment under a 12-month financing plan, in AZN | irshad, soliton, w-t.az |
| `installment_18m` | decimal string | Monthly payment under an 18-month financing plan, in AZN | irshad, soliton, w-t.az |
| `installment_monthly` | decimal string | Monthly payment for the default or currently shown financing plan, in AZN | bakuelectronics, birmarket, smartelectronics |
| `installment_term` | string | Duration of the default financing plan, e.g. `"12 ay"`, `"18 ay"` | bakuelectronics, birmarket, smartelectronics |
| `installment` | string | Raw installment text as scraped (not split into monthly/term) | kontakt, mgstore |
| `installment_active_term` | string | Currently selected installment term shown on the card, e.g. `"12 ay"` | w-t.az |
| `installment_active_price` | decimal string | Monthly payment for the active term, in AZN | w-t.az |
| `in_stock` | string | `"True"` if the product is available, `"False"` if out of stock, empty if unknown | smartelectronics, soliton, texnohome |
| `is_new` | string | `"True"` if the platform labels the product as newly added, `"False"` otherwise | bytelecom |
| `is_online` | string | `"True"` if the product is available for online purchase | bakuelectronics |
| `quantity` | integer string | Stock quantity available | bakuelectronics |
| `review_count` | integer string | Number of customer reviews | bakuelectronics |
| `rating` | decimal string | Average customer rating (typically 0–5) | bakuelectronics |
| `special_offer` | string | Promotional labels, offer text, badges, or campaign names. Multiple values are semicolon-separated | bakuelectronics (campaign), birmarket (implied), bytelecom (badges), irshad, smartelectronics (promo_labels), soliton, texnohome (labels), w-t.az (campaign) |
| `region` | string | Geographic region of the listing | tap.az |
| `updated_at` | string | ISO 8601 timestamp of when the listing was last updated | tap.az |
| `status` | string | Listing status (e.g. `"ACTIVE"`) | tap.az |
| `kinds` | string | Ad kind tags, comma-joined (e.g. `"STANDARD"`) | tap.az |
| `shop_id` | string | Shop/seller identifier on tap.az; empty for private listings | tap.az |
| `url` | string | Absolute URL to the product or listing page | All |
| `image_url` | string | Absolute URL to the primary product image | All |
| `page` | string | Page number (or offset/batch number) at which this product was collected | All (w-t.az has no pagination so this is empty) |

---

### Column Population Matrix

A `✓` means the column is populated for that source; `–` means it is always empty.

| Column | baku | birm | byte | irsh | kont | mgst | smar | soli | tap | texn | w-t |
|--------|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:----:|:---:|:----:|:---:|
| name | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| product_id | ✓ | ✓ | ✓ | ✓ | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| sku | ✓ | – | – | – | ✓ | ✓ | – | – | – | – | – |
| brand | – | – | – | – | ✓ | ✓ | – | ✓ | – | – | – |
| category | – | – | – | ✓ | ✓ | ✓ | ✓ | ✓ | – | – | – |
| price_current | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓* | ✓ |
| price_old | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | – | ✓ | – |
| discount_pct | – | ✓ | – | ✓ | ✓ | – | – | ✓ | – | ✓ | – |
| discount_amount | ✓ | – | – | ✓ | ✓ | ✓ | – | ✓ | – | – | – |
| installment_6m | – | – | – | ✓ | – | – | – | ✓ | – | – | ✓ |
| installment_12m | – | – | – | ✓ | – | – | – | ✓ | – | – | ✓ |
| installment_18m | – | – | – | ✓ | – | – | – | ✓ | – | – | ✓ |
| installment_monthly | ✓ | ✓ | – | – | – | – | ✓ | – | – | – | – |
| installment_term | ✓ | ✓ | – | – | – | – | ✓ | – | – | – | – |
| installment | – | – | – | – | ✓ | ✓ | – | – | – | – | – |
| installment_active_term | – | – | – | – | – | – | – | – | – | – | ✓ |
| installment_active_price | – | – | – | – | – | – | – | – | – | – | ✓ |
| in_stock | – | – | – | – | – | – | ✓ | ✓ | – | ✓ | – |
| is_new | – | – | ✓ | – | – | – | – | – | – | – | – |
| is_online | ✓ | – | – | – | – | – | – | – | – | – | – |
| quantity | ✓ | – | – | – | – | – | – | – | – | – | – |
| review_count | ✓ | – | – | – | – | – | – | – | – | – | – |
| rating | ✓ | – | – | – | – | – | – | – | – | – | – |
| special_offer | ✓ | – | ✓ | – | – | – | ✓ | ✓ | – | ✓ | ✓ |
| region | – | – | – | – | – | – | – | – | ✓ | – | – |
| updated_at | – | – | – | – | – | – | – | – | ✓ | – | – |
| status | – | – | – | – | – | – | – | – | ✓ | – | – |
| kinds | – | – | – | – | – | – | – | – | ✓ | – | – |
| shop_id | – | – | – | – | – | – | – | – | ✓ | – | – |
| url | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| image_url | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| page | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓* | ✓* | ✓ | – |

\* texnohome `price_current` = `"0.00"` for out-of-stock items; filter with `price > 1.0` for analysis.
\* soliton `page` = scrape offset (0, 15, 30 …), not page number.
\* tap.az `page` = batch number (sequential page index).

---

## 2. Per-Source CSVs

### `data/irshad.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `code` | Irshad product code (→ `product_id` in data.csv) |
| `price_current` | Sale price in AZN |
| `price_old` | Original price in AZN |
| `discount_pct` | Discount percentage string |
| `discount_amount` | Absolute discount in AZN |
| `availability` | `"Var"` (in stock) / `"Yoxdur"` (out of stock) (→ `in_stock` in data.csv) |
| `installment_6m` | Monthly payment at 6 months |
| `installment_12m` | Monthly payment at 12 months |
| `installment_18m` | Monthly payment at 18 months |
| `product_type` | Category string (→ `category` in data.csv) |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

### `data/kontakt.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `brand` | Brand name |
| `sku` | Product SKU (stock-keeping unit) |
| `price_current` | Sale price in AZN |
| `price_old` | Original price in AZN |
| `discount_pct` | Discount percentage |
| `discount_amount` | Absolute discount in AZN |
| `installment` | Raw installment text (e.g. `"41.66 AZN x 12 ay"`) |
| `category` | Category label |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

### `data/smartelectronics.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Product ID |
| `category` | Category label |
| `price_current` | Current price in AZN |
| `price_old` | Original price in AZN (empty if no discount) |
| `installment_monthly` | Monthly payment in AZN |
| `installment_term` | Financing duration (e.g. `"12 ay"`) |
| `in_stock` | `"True"` / `"False"` |
| `promo_labels` | Promotional label text (→ `special_offer` in data.csv) |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Page index (0-based) |

---

### `data/bakuelectronics.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Product ID |
| `sku` | Product SKU |
| `price_current` | Sale price in AZN |
| `price_old` | Original price in AZN |
| `discount_amount` | Absolute discount in AZN |
| `installment_monthly` | Monthly payment in AZN |
| `installment_term` | Financing duration |
| `quantity` | Units available in stock |
| `review_count` | Number of customer reviews |
| `rating` | Average rating (0–5) |
| `is_online` | `"True"` if orderable online |
| `campaign` | Campaign / promotion label (→ `special_offer` in data.csv) |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

### `data/mgstore.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Product ID |
| `sku` | Product SKU |
| `brand` | Brand name |
| `price_current` | Sale price in AZN |
| `price_old` | Original price in AZN |
| `discount_amount` | Absolute discount in AZN |
| `installment` | Raw installment text |
| `category` | Category label |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

### `data/birmarket.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Product ID |
| `price_current` | Sale price in AZN (empty for price-on-request listings) |
| `price_old` | Original price in AZN |
| `discount_pct` | Discount percentage |
| `installment_monthly` | Monthly payment in AZN |
| `installment_term` | Financing duration |
| `url` | Listing URL |
| `image_url` | Listing image URL |
| `page` | Listing page number |

---

### `data/tapaz.csv`

| Column | Description |
|--------|-------------|
| `title` | Ad title (→ `name` in data.csv) |
| `product_id` | Legacy resource ID (numeric) |
| `price` | Asking price in AZN (→ `price_current` in data.csv) |
| `region` | Geographic region of the seller |
| `updated_at` | ISO 8601 timestamp of last update |
| `kinds` | Ad kind tags (comma-joined) |
| `status` | Ad status (e.g. `"ACTIVE"`) |
| `shop_id` | Seller shop ID; empty for private sellers |
| `url` | Ad page URL |
| `image_url` | Primary image URL |
| `batch` | Batch (page) number during scrape (→ `page` in data.csv) |

---

### `data/wtaz.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Platform product ID |
| `price` | Current price in AZN (→ `price_current` in data.csv) |
| `installment_6m` | Monthly payment at 6 months |
| `installment_12m` | Monthly payment at 12 months |
| `installment_18m` | Monthly payment at 18 months |
| `installment_active_term` | Currently displayed term (e.g. `"12 ay"`) |
| `installment_active_price` | Monthly payment for the active term |
| `campaign` | Campaign / offer label (→ `special_offer` in data.csv) |
| `url` | Product page URL |
| `image_url` | Product image URL |

---

### `data/soliton.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Product ID |
| `brand_id` | Brand identifier (→ `brand` in data.csv) |
| `price_current` | Current price in AZN |
| `price_old` | Original price in AZN |
| `discount_pct` | Discount percentage |
| `discount_amount` | Absolute discount in AZN |
| `installment_6m` | Monthly payment at 6 months |
| `installment_12m` | Monthly payment at 12 months |
| `installment_18m` | Monthly payment at 18 months |
| `in_stock` | `"True"` / `"False"` |
| `special_offer` | Special offer / promotion text |
| `category` | Category label |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `offset` | Scrape offset value (→ `page` in data.csv) |

---

### `data/bytelecom.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Livewire product model ID |
| `price_current` | Sale price in AZN (the lower / discounted price) |
| `price_old` | Original price in AZN (the higher / pre-discount price) |
| `badges` | Promotional badge texts, semicolon-separated (→ `special_offer` in data.csv) |
| `is_new` | `"True"` if labelled as a new arrival |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

### `data/texnohome.csv`

| Column | Description |
|--------|-------------|
| `name` | Product name |
| `product_id` | Platform product ID |
| `price_current` | Current price in AZN; `"0.00"` for out-of-stock items |
| `price_old` | Original price in AZN |
| `discount_pct` | Discount percentage (e.g. `"-16%"`) |
| `in_stock` | `"True"` / `"False"` |
| `labels` | Offer/campaign label texts, semicolon-separated (→ `special_offer` in data.csv) |
| `url` | Product page URL |
| `image_url` | Product image URL |
| `page` | Listing page number |

---

## 3. Price Field Conventions

All price fields are stored as **decimal strings** (e.g. `"499.00"`, `"1249.99"`), not as floats. This preserves the original precision and avoids floating-point conversion artefacts.

When loading for analysis, cast with `float(row["price_current"])` and filter with `price > 1.0` to exclude:
- `"0.00"` — out-of-stock items on texnohome.az
- `"0.01"` — data placeholder on kontakt.az

Currency is always **AZN (Azerbaijani manat, ₼)** unless stated otherwise.
