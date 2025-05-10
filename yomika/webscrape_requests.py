from dataclasses import dataclass
import time
from typing import Dict, Optional, Union, Any, Tuple
import logging

import requests
import backoff

from . import defaults
from .modules.url_validator import is_valid_url
from .modules.utils import backoff_handler_generic

Defaults = defaults.Defaults

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

class InvalidURLError(Exception):
    """Exception raised when the URL is invalid."""
    pass

class WebPageLoadError(Exception):
    """Exception raised when a web page fails to load."""
    pass

class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass

class ContentTypeError(Exception):
    """Exception raised when the content type is unexpected."""
    pass


class RequestRateLimiter:
    """Simple rate limiter for web requests."""

    def __init__(self, requests_per_second: float = Defaults.DEFAULT_RPS_LIMIT):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum number of requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0

    def wait(self):
        """Wait if necessary to respect the rate limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_interval:
            sleep_time = self.min_interval - time_since_last_request
            time.sleep(sleep_time)

        self.last_request_time = time.time()



@backoff.on_exception(
    backoff.expo,
    exception=(WebPageLoadError,
        requests.RequestException,
        RateLimitExceededError,
        ConnectionError),
    max_tries=Defaults.DEFAULT_MAX_RETRIES,
    max_time=Defaults.DEFAULT_MAX_TIME,
    on_backoff=backoff_handler_generic)
def webscrape_requests(
        url: str,
        custom_headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: int = Defaults.DEFAULT_REQ_TIMEOUT,
        allow_redirects: bool = True,
        verify_ssl: bool = True,
        expected_content_type: Optional[str] = None,
        proxy: Optional[Dict[str, str]] = None,
        rate_limiter: Optional[RequestRateLimiter] = None
) -> ScrapedResponse:
    """
    Fetch DOM contents of a web page. SSRed HTML only, Cannot handle JS/CSR.

    Args:
        url: URL to scrape
        custom_headers: Custom HTTP headers to send with the request
        params: URL parameters for the request
        cookies: Cookies to send with the request
        timeout: Request timeout in seconds
        allow_redirects: Whether to follow redirects
        verify_ssl: Whether to verify SSL certificates
        expected_content_type: Expected content type (e.g., 'text/html')
        proxy: Proxy configuration dict (e.g., {'http': 'http://proxy.com:8080'})
        rate_limiter: Optional rate limiter object

    Returns:
        ScrapedResponse: Object containing the response and metadata

    Raises:
        InvalidURLError: If the URL is not valid
        WebPageLoadError: If there was an error loading the web page
        ContentTypeError: If the content type doesn't match expected type
    """
    start_time = time.time()
    error_message = None

    if rate_limiter:
        rate_limiter.wait()

    # Validate URL
    if not is_valid_url(url):
        raise InvalidURLError(f"Invalid URL format: {url}")

    # Set up headers
    headers = custom_headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    try:
        with requests.Session() as session:
            response = session.get(
                url,
                headers=headers,
                params=params,
                cookies=cookies,
                timeout=timeout,
                allow_redirects=allow_redirects,
                verify=verify_ssl,
                proxies=proxy
            )

            # Raise for HTTP errors
            response.raise_for_status()

            # Check content type if expected type is provided
            if expected_content_type and expected_content_type not in response.headers.get('Content-Type', ''):
                raise ContentTypeError(
                    f"Expected content type '{expected_content_type}' but got "
                    f"'{response.headers.get('Content-Type')}'"
                )

            # Get actual response time
            elapsed_time = time.time() - start_time

            # Check for common rate limiting status codes
            if response.status_code in (429, 503):
                raise RateLimitExceededError(f"Rate limit exceeded: {response.status_code}")

            return ScrapedResponse(
                url=url,
                status_code=response.status_code,
                content=response.content,
                text=response.text,
                headers=dict(response.headers),
                elapsed_time=elapsed_time,
                content_type=response.headers.get('Content-Type', ''),
                success=True
            )

    except requests.exceptions.ConnectionError as e:
        error_message = f"Connection error for {url}: {str(e)}"
        logging.error(error_message)
        raise WebPageLoadError(error_message)

    except requests.exceptions.Timeout as e:
        error_message = f"Timeout error for {url}: {str(e)}"
        logging.error(error_message)
        raise WebPageLoadError(error_message)

    except requests.exceptions.TooManyRedirects as e:
        error_message = f"Too many redirects for {url}: {str(e)}"
        logging.error(error_message)
        raise WebPageLoadError(error_message)

    except requests.exceptions.HTTPError as e:
        error_message = f"HTTP error for {url}: {str(e)}"
        logging.error(error_message)
        raise WebPageLoadError(error_message)

    except ContentTypeError as e:
        error_message = str(e)
        logging.error(error_message)
        raise

    except Exception as e:
        error_message = f"Unexpected error while loading {url}: {str(e)}"
        logging.error(error_message)
        raise WebPageLoadError(error_message)

    # This code shouldn't be reached
    return ScrapedResponse(
        url=url,
        status_code=0,
        content=b'',
        text='',
        headers={},
        elapsed_time=time.time() - start_time,
        content_type='',
        success=False,
        error=error_message
    )


if __name__ == "__main__":
    pass
