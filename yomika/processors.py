import asyncio
import inspect
import concurrent.futures
from typing import Coroutine, Callable

import aiohttp

from .custom_dataclasses import ScrapedResponse, WebscrapeConfig
from .webscrape_requests import webscrape_requests
from .webscrape_aiohttp import webscrape_aiohttp


def run_async(coro: Coroutine):
    """Safely run an async function from any context without affecting the application.

    Args:
        coro: A coroutine object to run

    Returns:
        The result of the coroutine execution
    """
    # Type checking
    if not inspect.iscoroutine(coro) and not inspect.isawaitable(coro):
        raise TypeError(f"Expected a coroutine or awaitable, got {type(coro).__name__}")

    # Always use a separate thread with its own event loop
    # This is the safest approach for a module
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(lambda: asyncio.run(coro))
        return future.result()


def scrape_url_list_sync(url_list: list[str]) -> list[ScrapedResponse]:
    return [webscrape_requests(url) for url in url_list]


def scrape_url_list_async(
        url_list: list[str],
        config: WebscrapeConfig = WebscrapeConfig,
        on_success: Callable = None,
        on_failure: Callable = None
) -> list[ScrapedResponse]:
    async def process_async_scrape():

        async with aiohttp.ClientSession() as session:

            tasks = [webscrape_aiohttp(
                url=url,
                session=session,
                config=config,
                on_success=on_success,
                on_failure=on_failure
            ) for url in url_list]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    raise result

            return results

    return run_async(process_async_scrape())
