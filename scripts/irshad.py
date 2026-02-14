"""
irshad.az tablet scraper
Uses asyncio + aiohttp (curl_cffi fallback for Cloudflare)

The site loads products via AJAX (PJAX):
  Listing page : GET /az/notbuk-planset-ve-komputer-texnikasi/plansetler
  AJAX pages   : GET /az/list-products/notbuk-planset-ve-komputer-texnikasi/plansetler?page=N
  Headers      : X-Requested-With: XMLHttpRequest
                 X-CSRF-Token: <from meta tag>
Pagination stops when the response contains no #loadMore button.
"""

import asyncio
import csv
import re
from pathlib import Path

import aiohttp
from bs4 import BeautifulSoup

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_CSV = DATA_DIR / "irshad.csv"

# ── constants ────────────────────────────────────────────────────────────────
BASE_URL       = "https://irshad.az"
LISTING_URL    = f"{BASE_URL}/az/notbuk-planset-ve-komputer-texnikasi/plansetler"
AJAX_URL       = f"{BASE_URL}/az/list-products/notbuk-planset-ve-komputer-texnikasi/plansetler"
CONCURRENCY    = 3
DELAY          = 1.0

COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "az,en-US;q=0.9,en;q=0.8,ru;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Chromium";v="124","Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}

CSV_FIELDS = [
    "name",
    "code",
    "price_current",
    "price_old",
    "discount_pct",
    "discount_amount",
    "availability",
    "installment_6m",
    "installment_12m",
    "installment_18m",
    "product_type",
    "url",
    "image_url",
    "page",
]


# ── helpers ──────────────────────────────────────────────────────────────────

def clean_price(text: str) -> str:
    """'649.99 AZN' → '649.99'"""
    return re.sub(r"[^\d.]", "", text.replace(",", ".")).strip()


def parse_products(html: str, page_num: int) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for card in soup.select("div.product"):
        # skip nested or utility divs that aren't product cards
        classes = " ".join(card.get("class", []))
        if "product__" in classes:
            continue

        # ── name & URL ───────────────────────────────────────────────────
        name_link = card.select_one("a.product__name.product-link")
        if not name_link:
            continue
        name = name_link.get_text(strip=True)
        url  = name_link.get("href", "")

        # ── product type (Planşet / etc.) ─────────────────────────────
        type_el = card.select_one(".product__type")
        product_type = type_el.get_text(strip=True) if type_el else ""

        # ── product code ──────────────────────────────────────────────
        # Use data-code from the basket button of the active variant
        basket_btns = card.select("a.product-add-to-cart[data-code]")
        # The active product__flex-right is the one without d-none
        active_right = card.select_one(
            ".product__flex-right:not(.d-none), .product__flex-right"
        )
        code = ""
        if active_right:
            btn = active_right.select_one("a.product-add-to-cart[data-code]")
            if btn:
                code = btn.get("data-code", "")
        if not code and basket_btns:
            code = basket_btns[0].get("data-code", "")

        # ── prices ────────────────────────────────────────────────────
        price_current = price_old = ""
        price_block = None
        if active_right:
            price_block = active_right.select_one(".product__price__current")
        if not price_block:
            price_block = card.select_one(".product__price__current")
        if price_block:
            new_el = price_block.select_one(".new-price")
            old_el = price_block.select_one(".old-price")
            if new_el:
                price_current = clean_price(new_el.get_text())
            if old_el:
                price_old = clean_price(old_el.get_text())

        # ── discount % ────────────────────────────────────────────────
        disc_el = card.select_one(".product-discount-text")
        discount_pct = disc_el.get_text(strip=True) if disc_el else ""

        # ── discount amount label (e.g. "-150 AZN") ───────────────────
        disc_amt_el = card.select_one(".product__label--orange")
        discount_amount = disc_amt_el.get_text(strip=True) if disc_amt_el else ""

        # ── availability ──────────────────────────────────────────────
        avail_el = card.select_one(
            ".product__label--light-purple, .product__label--light-orange"
        )
        availability = avail_el.get_text(strip=True) if avail_el else ""

        # ── installment options (6 / 12 / 18 ay monthly payments) ─────
        inst: dict[str, str] = {}
        if active_right:
            for inp in active_right.select("input.ppl-input[data-monthly-payment]"):
                label_id = inp.get("id", "")
                label_el = active_right.select_one(f'label[for="{label_id}"]')
                months = label_el.get_text(strip=True) if label_el else ""
                monthly = inp.get("data-monthly-payment", "")
                if "6" in months:
                    inst["6"] = monthly
                elif "12" in months:
                    inst["12"] = monthly
                elif "18" in months:
                    inst["18"] = monthly

        # ── image ─────────────────────────────────────────────────────
        img_el = card.select_one(".product__img img")
        image_url = img_el.get("src", "") if img_el else ""

        products.append({
            "name":            name,
            "code":            code,
            "price_current":   price_current,
            "price_old":       price_old,
            "discount_pct":    discount_pct,
            "discount_amount": discount_amount,
            "availability":    availability,
            "installment_6m":  inst.get("6", ""),
            "installment_12m": inst.get("12", ""),
            "installment_18m": inst.get("18", ""),
            "product_type":    product_type,
            "url":             url,
            "image_url":       image_url,
            "page":            page_num,
        })

    return products


def has_more_pages(html: str) -> bool:
    """True if the HTML contains a Load More button (i.e. more pages exist)."""
    soup = BeautifulSoup(html, "html.parser")
    btn = soup.select_one("#loadMore")
    return btn is not None


def get_csrf_token(html: str) -> str:
    """Extract CSRF token from <meta name='csrf-token'>."""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.select_one('meta[name="csrf-token"]')
    return meta.get("content", "") if meta else ""


# ── async fetch ──────────────────────────────────────────────────────────────

async def bootstrap_session(session: aiohttp.ClientSession) -> str:
    """
    Fetch the main listing page to prime cookies and retrieve CSRF token.
    Returns the CSRF token string.
    """
    headers = {**COMMON_HEADERS, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"}
    async with session.get(LISTING_URL, headers=headers) as resp:
        resp.raise_for_status()
        html = await resp.text()
        token = get_csrf_token(html)
        print(f"  Session primed — CSRF token: {token[:16]}…")
        # parse page 1 from the listing page too
        return token, html


async def fetch_ajax_page(
    session: aiohttp.ClientSession,
    page: int,
    csrf_token: str,
    sem: asyncio.Semaphore,
) -> tuple[int, str]:
    """Fetch one AJAX product page."""
    params = {"page": page}
    headers = {
        **COMMON_HEADERS,
        "Accept": "*/*",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRF-Token": csrf_token,
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Site": "same-origin",
        "Referer": LISTING_URL,
    }
    async with sem:
        await asyncio.sleep(DELAY)
        async with session.get(AJAX_URL, params=params, headers=headers) as resp:
            resp.raise_for_status()
            html = await resp.text()
            print(f"  Fetched page {page}  [status {resp.status}]")
            return page, html


# ── main scrape logic ────────────────────────────────────────────────────────

async def scrape_all() -> list[dict]:
    connector = aiohttp.TCPConnector(ssl=False)
    timeout   = aiohttp.ClientTimeout(total=30)
    sem       = asyncio.Semaphore(CONCURRENCY)
    all_products: list[dict] = []

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # ── step 1: prime session cookies + get CSRF token ───────────
            csrf_token, _ = await bootstrap_session(session)

            # ── step 2: all products come from the AJAX endpoint (page=1+)
            # Fetch page 1 first to check loadMore, then batch the rest.
            _, html1 = await fetch_ajax_page(session, 1, csrf_token, asyncio.Semaphore(1))
            prods1 = parse_products(html1, 1)
            all_products.extend(prods1)
            print(f"  Page 1: {len(prods1)} products")

            if not has_more_pages(html1):
                return all_products

            # ── step 3: walk remaining AJAX pages concurrently ───────────
            page = 2
            while True:
                tasks = [
                    fetch_ajax_page(session, p, csrf_token, sem)
                    for p in range(page, page + CONCURRENCY)
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                found_more = False
                for result in sorted(
                    [r for r in results if not isinstance(r, Exception)],
                    key=lambda x: x[0]
                ):
                    p_num, html = result
                    prods = parse_products(html, p_num)
                    all_products.extend(prods)
                    print(f"  Page {p_num}: {len(prods)} products")
                    page = max(page, p_num + 1)
                    # Overwrite: only the LAST processed page determines whether to continue
                    found_more = bool(prods) and has_more_pages(html)
                    if not found_more:
                        break   # no point inspecting further pages in this batch
                for result in results:
                    if isinstance(result, Exception):
                        print(f"  [warn] {result}")

                if not found_more:
                    break

    except aiohttp.ClientResponseError as exc:
        if exc.status == 403:
            print("\n  [403] Cloudflare blocked aiohttp — falling back to curl_cffi …\n")
            return await scrape_all_cffi()
        raise

    return all_products


# ── curl_cffi fallback ────────────────────────────────────────────────────────

async def scrape_all_cffi() -> list[dict]:
    from curl_cffi.requests import AsyncSession

    sem = asyncio.Semaphore(CONCURRENCY)
    all_products: list[dict] = []

    async def fetch_cffi_ajax(s, page: int) -> tuple[int, str]:
        params  = {"page": page}
        headers = {
            **COMMON_HEADERS,
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-Token": csrf_token,
            "Referer": LISTING_URL,
        }
        async with sem:
            await asyncio.sleep(DELAY)
            resp = await s.get(AJAX_URL, params=params, headers=headers)
            resp.raise_for_status()
            print(f"  [cffi] Fetched page {page}  [{resp.status_code}]")
            return page, resp.text

    async with AsyncSession(impersonate="chrome124") as s:
        # prime
        r = await s.get(
            LISTING_URL,
            headers={**COMMON_HEADERS, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
        )
        csrf_token = get_csrf_token(r.text)
        html1      = r.text
        print(f"  [cffi] Session primed — CSRF: {csrf_token[:16]}…")

        prods1 = parse_products(html1, 1)
        all_products.extend(prods1)
        print(f"  Page 1 (listing): {len(prods1)} products")

        if not has_more_pages(html1):
            return all_products

        page = 2
        while True:
            tasks  = [fetch_cffi_ajax(s, p) for p in range(page, page + CONCURRENCY)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            found_more = False
            for result in results:
                if isinstance(result, Exception):
                    print(f"  [warn] {result}")
                    continue
                p_num, html = result
                prods = parse_products(html, p_num)
                all_products.extend(prods)
                print(f"  Page {p_num}: {len(prods)} products")
                if has_more_pages(html):
                    found_more = True
                page = max(page, p_num + 1)

            if not found_more:
                break

    return all_products


# ── CSV ───────────────────────────────────────────────────────────────────────

def save_csv(products: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(products)
    print(f"\nSaved {len(products)} products → {path}")


# ── entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    print(f"Scraping: {LISTING_URL}")
    products = await scrape_all()

    if not products:
        print("No products found — check selectors or connectivity.")
        return

    # deduplicate by code+url
    seen: set[str] = set()
    unique = []
    for p in products:
        key = p["code"] or p["url"]
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
        elif not key:
            unique.append(p)

    print(f"\nTotal unique products: {len(unique)}")
    save_csv(unique, OUTPUT_CSV)


if __name__ == "__main__":
    asyncio.run(main())
