import asyncio
import logging
import os
import random

import httpx

from .config import Config, Product, Settings
from .parsers import get_parser
from .parsers.base import BaseParser, ParseResult
from .stealth import get_random_headers, get_random_delay

logger = logging.getLogger(__name__)


async def scrape_url(
    url: str, parser: BaseParser, client: httpx.AsyncClient
) -> ParseResult:
    """Scrape a URL using httpx with stealth headers."""
    headers = get_random_headers(url)
    try:
        response = await client.get(
            url, headers=headers, timeout=30.0, follow_redirects=True
        )
        response.raise_for_status()
        return parser.extract_price(response.text, url)
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return ParseResult(price=None, name=None, available=False)
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return ParseResult(price=None, name=None, available=False)


async def scrape_with_firecrawl(
    url: str, parser: BaseParser, api_key: str
) -> ParseResult:
    """Fallback: scrape using Firecrawl API (costs 1 credit)."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "formats": ["html"],
        "waitFor": 3000,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            html = data.get("data", {}).get("html", "")
            if html:
                return parser.extract_price(html, url)
            # Try markdown fallback — extract price from text
            md = data.get("data", {}).get("markdown", "")
            if md:
                from .utils.price import parse_price as pp
                import re
                prices = re.findall(r'R\$\s*[\d.,]+', md)
                if prices:
                    parsed = pp(prices[0])
                    if parsed:
                        return ParseResult(
                            price=parsed, name=None, available=True,
                            original_text=prices[0],
                        )
            return ParseResult(price=None, name=None, available=False)
    except Exception as e:
        logger.error(f"Firecrawl error for {url}: {e}")
        return ParseResult(price=None, name=None, available=False)


async def scrape_product(
    product: Product,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    settings: Settings,
) -> dict[str, ParseResult]:
    """Scrape all store links for a single product."""
    results: dict[str, ParseResult] = {}
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")

    for link in product.links:
        url = str(link.url)
        parser = get_parser(url)
        if not parser:
            logger.warning(f"No parser found for {url}")
            results[link.store] = ParseResult(
                price=None, name=None, available=False
            )
            continue

        async with semaphore:
            # Random delay to avoid rate limits
            delay = get_random_delay(*settings.request_delay)
            await asyncio.sleep(delay)

            # Try httpx first
            result = await scrape_url(url, parser, client)

            # Fallback to Firecrawl if httpx failed
            if (result.price is None or not result.available) and settings.firecrawl_enabled and firecrawl_key:
                logger.info(f"Falling back to Firecrawl for {url}")
                result = await scrape_with_firecrawl(url, parser, firecrawl_key)

            results[link.store] = result
            logger.info(
                f"  {link.store}: "
                f"{'R$ ' + f'{result.price:.2f}' if result.price else 'N/A'} "
                f"({'available' if result.available else 'unavailable'})"
            )

    return results


async def run_all(config: Config) -> dict[str, dict[str, ParseResult]]:
    """Scrape all active products concurrently."""
    semaphore = asyncio.Semaphore(config.settings.max_concurrent)
    results: dict[str, dict[str, ParseResult]] = {}

    async with httpx.AsyncClient(http2=True) as client:
        tasks = {
            product.id: scrape_product(product, client, semaphore, config.settings)
            for product in config.products
            if product.active
        }

        # Run all products concurrently
        gathered = await asyncio.gather(
            *tasks.values(), return_exceptions=True
        )

        for product_id, result in zip(tasks.keys(), gathered):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape product {product_id}: {result}")
                results[product_id] = {}
            else:
                results[product_id] = result

    return results
