from dataclasses import dataclass
from typing import Dict, Optional, Any

from .defaults import Defaults
from .modules.rate_limiter import RequestRateLimiter

@dataclass
class WebscrapeConfig:
    custom_headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    cookies: Optional[Dict[str, str]] = None
    timeout: int = Defaults.DEFAULT_REQ_TIMEOUT
    allow_redirects: bool = True
    verify_ssl: bool = True
    expected_content_type: Optional[str] = None
    proxy: Optional[str] = None
    rate_limiter: Optional["RequestRateLimiter"] = RequestRateLimiter()

@dataclass
class ScrapedResponse:
    """Data class for storing scraping results with metadata."""
    url: str
    status_code: int
    content: bytes
    text: str
    headers: Dict[str, str]
    elapsed_time: float
    content_type: str
    success: bool
    error: Optional[str] = None
