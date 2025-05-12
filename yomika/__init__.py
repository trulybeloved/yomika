from .__version__ import __version__

from .webscrape_requests import webscrape_requests
from .webscrape_aiohttp import webscrape_aiohttp
from .processors import scrape_url_list_sync, scrape_url_list_async
from .classes import WebscrapeConfig, ScrapedResponse
from .defaults import Defaults
from .modules.rate_limiter import RequestRateLimiter
from .modules.url_validator import URLValidator, is_valid_url
from .modules.check_connectivity import InternetConnectivityChecker, is_connected

__all__ = [
    "webscrape_requests",
    "webscrape_aiohttp",
    "scrape_url_list_sync",
    "scrape_url_list_async",
    "WebscrapeConfig",
    "ScrapedResponse",
    "Defaults",
    "RequestRateLimiter",
    "URLValidator",
    "is_valid_url",
    "InternetConnectivityChecker",
    "is_connected",
]