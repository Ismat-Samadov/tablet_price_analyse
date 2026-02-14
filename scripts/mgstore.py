"""
mgstore.az tablet scraper
Uses asyncio + aiohttp (with curl_cffi for Cloudflare bypass)

Pagination: GET /plansetler/plansetler?p=N  (1-indexed)
Total pages derived from the last numbered link in .pages ul,
and confirmed by the product count in .catalog__count.

Each product card  (.prodItem)  carries a data-gtm JSON attribute
with structured product metadata — no fragile DOM text parsing needed.
"""

import asyncio
import csv
import json
import re
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = DATA_DIR / "mgstore.csv"

# ── constants ────────────────────────────────────────────────────────────────
BASE_URL     = "https://mgstore.az"
CATEGORY_URL = f"{BASE_URL}/plansetler/plansetler"
CONCURRENCY  = 3
DELAY        = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/144.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "az,en-US;q=0.9,en;q=0.8,ru;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Referer": BASE_URL + "/",
    "sec-ch-ua": '"Not(A:Brand";v="8","Chromium";v="144","Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "DNT": "1",
}

CSV_FIELDS = [
    "name",
    "product_id",
    "sku",
    "brand",
    "price_current",
    "price_old",
    "discount_amount",
    "installment",
    "category",
    "url",
    "image_url",
    "page",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def clean_price(text: str) -> str:
    """
    Handles both  '329,99 ₼'  and  '1.899,99 ₼'  (dot = thousands sep).
    Returns a plain decimal string, e.g. '329.99' or '1899.99'.
    """
    # Strip currency symbols and whitespace
    text = re.sub(r"[^\d,.]", "", text).strip()
    # If there's a comma, dots are thousands separators → remove them
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    # If multiple dots remain (e.g. '1.899.99' edge case), keep only last
    parts = text.split(".")
    if len(parts) > 2:
        text = "".join(parts[:-1]) + "." + parts[-1]
    return text


def parse_products(html: str, page_num: int) -> list[dict]:
    """Extract all product dicts from one page of HTML."""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select(".prodItem"):
        # ── GTM data (name, sku, brand, price, discount, category) ───────
        gtm_raw = item.get("data-gtm", "{}")
        try:
            gtm = json.loads(gtm_raw)
        except json.JSONDecodeError:
            gtm = {}

        name     = gtm.get("item_name", "").strip()
        sku      = gtm.get("item_id", item.get("data-sku", "")).strip()
        brand    = gtm.get("item_brand", "").strip()
        category = gtm.get("item_category", "").strip()
        # GTM price is the OLD price, discount is the saving amount
        price_old_gtm    = str(gtm.get("price", "")).strip()
        discount_amount  = str(gtm.get("discount", "")).strip()

        # ── product ID (from element id attr) ─────────────────────────
        product_id = item.get("id", "").strip()

        # ── fallback name from DOM ─────────────────────────────────────
        if not name:
            title_el = item.select_one(".prodItem__title")
            name = title_el.get_text(strip=True) if title_el else ""

        # ── prices from DOM ───────────────────────────────────────────
        price_current = ""
        price_old     = price_old_gtm
        prices_el = item.select_one(".prodItem__prices")
        if prices_el:
            old_el = prices_el.select_one("i")
            cur_el = prices_el.select_one("b")
            if old_el:
                price_old = clean_price(old_el.get_text())
            if cur_el:
                price_current = clean_price(cur_el.get_text())

        # ── installment label (e.g. "0% 6 ay") ───────────────────────
        inst_el = item.select_one(".prodItem__prices span")
        installment = inst_el.get_text(strip=True) if inst_el else ""

        # ── URL ───────────────────────────────────────────────────────
        url = ""
        img_link = item.select_one("a.prodItem__img[href]")
        if img_link:
            href = img_link.get("href", "")
            url = href if href.startswith("http") else BASE_URL + href

        # ── image (prefer webp source, fallback to img src) ───────────
        image_url = ""
        pic = item.select_one("picture.product-image")
        if pic:
            src_el = pic.select_one("source[srcset]")
            if src_el:
                image_url = src_el.get("srcset", "").split(",")[0].strip()
        if not image_url:
            img_el = item.select_one("img.product-image")
            if img_el:
                image_url = img_el.get("src", "")

        products.append({
            "name":            name,
            "product_id":      product_id,
            "sku":             sku,
            "brand":           brand,
            "price_current":   price_current,
            "price_old":       price_old,
            "discount_amount": discount_amount,
            "installment":     installment,
            "category":        category,
            "url":             url,
            "image_url":       image_url,
            "page":            page_num,
        })

    return products


def get_total_pages(html: str) -> int:
    """Derive the last page number from the .pages pagination block."""
    soup = BeautifulSoup(html, "html.parser")

    # Collect all page numbers from links like ?p=N
    nums = []
    for a in soup.select(".pages a.page[href]"):
        m = re.search(r"[?&]p=(\d+)", a.get("href", ""))
        if m:
            nums.append(int(m.group(1)))

    if nums:
        last = max(nums)
        print(f"  Total pages: {last}")
        return last

    # Fallback: read total count from .catalog__count e.g. "(54)"
    count_el = soup.select_one(".catalog__count")
    if count_el:
        m = re.search(r"\d+", count_el.get_text())
        if m:
            total = int(m.group())
            # mgstore shows 20 products per page
            pages = (total + 19) // 20
            print(f"  Total products: {total}  →  {pages} page(s)")
            return pages

    return 1


# ── async fetch ──────────────────────────────────────────────────────────────

async def fetch_page(
    session: aiohttp.ClientSession,
    page: int,
    sem: asyncio.Semaphore,
) -> tuple[int, str]:
    """Fetch a single listing page; return (page_number, html)."""
    url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}?p={page}"
    async with sem:
        await asyncio.sleep(DELAY)
        async with session.get(url, headers=HEADERS, ssl=False) as resp:
            resp.raise_for_status()
            html = await resp.text()
            print(f"  Fetched page {page}  [status {resp.status}]")
            return page, html


async def scrape_all() -> list[dict]:
    """Orchestrate fetching all pages concurrently and parsing products."""
    sem = asyncio.Semaphore(CONCURRENCY)
    all_products: list[dict] = []

    connector = aiohttp.TCPConnector(ssl=False)
    timeout   = aiohttp.ClientTimeout(total=15, connect=8)

    try:
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Step 1: fetch page 1 to discover total pages
            print("Fetching page 1 …")
            _, html1 = await fetch_page(session, 1, asyncio.Semaphore(1))
            total_pages = get_total_pages(html1)
            prods1 = parse_products(html1, 1)
            all_products.extend(prods1)
            print(f"  Page 1: {len(prods1)} products")

            if total_pages < 2:
                return all_products

            # Step 2: fetch remaining pages concurrently
            print(f"Fetching pages 2–{total_pages} (concurrency={CONCURRENCY}) …")
            tasks = [fetch_page(session, p, sem) for p in range(2, total_pages + 1)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    print(f"  [warn] page fetch error: {result}")
                    continue
                page_num, html = result
                prods = parse_products(html, page_num)
                all_products.extend(prods)
                print(f"  Page {page_num}: {len(prods)} products")

    except (aiohttp.ClientResponseError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as e:
        status = getattr(e, "status", None)
        if status == 403 or status is None:
            reason = f"[{status}]" if status else "[timeout/connection error]"
            print(
                f"\n  {reason} Cloudflare blocked aiohttp — "
                "falling back to curl_cffi …\n"
            )
            return await scrape_all_cffi()
        raise

    return all_products


# ── curl_cffi fallback (Chrome TLS impersonation) ────────────────────────────

async def scrape_all_cffi() -> list[dict]:
    """Fallback: use curl_cffi async to bypass Cloudflare."""
    from curl_cffi.requests import AsyncSession

    all_products: list[dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async def fetch_cffi(s, page: int) -> tuple[int, str]:
        url = CATEGORY_URL if page == 1 else f"{CATEGORY_URL}?p={page}"
        async with sem:
            await asyncio.sleep(DELAY)
            resp = await s.get(url, headers=HEADERS)
            resp.raise_for_status()
            print(f"  [cffi] Fetched page {page}  [{resp.status_code}]")
            return page, resp.text

    async with AsyncSession(impersonate="chrome124") as session:
        await session.get(BASE_URL, headers=HEADERS)   # prime cookies

        print("Fetching page 1 (cffi) …")
        _, html1 = await fetch_cffi(session, 1)
        total_pages = get_total_pages(html1)
        prods1 = parse_products(html1, 1)
        all_products.extend(prods1)
        print(f"  Page 1: {len(prods1)} products")

        if total_pages >= 2:
            tasks = [fetch_cffi(session, p) for p in range(2, total_pages + 1)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"  [warn] {result}")
                    continue
                page_num, html = result
                prods = parse_products(html, page_num)
                all_products.extend(prods)
                print(f"  Page {page_num}: {len(prods)} products")

    return all_products


# ── CSV writer ────────────────────────────────────────────────────────────────

def save_csv(products: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(products)
    print(f"\nSaved {len(products)} products → {path}")


# ── entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    print(f"Scraping: {CATEGORY_URL}")
    products = await scrape_all()

    if not products:
        print("No products found — check selectors or connectivity.")
        return

    # Deduplicate by sku (falling back to url)
    seen: set[str] = set()
    unique = []
    for p in products:
        key = p["sku"] or p["url"]
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
        elif not key:
            unique.append(p)

    print(f"\nTotal unique products: {len(unique)}")
    save_csv(unique, OUTPUT_CSV)


if __name__ == "__main__":
    asyncio.run(main())
