import time
from typing import Dict, Optional, Any
import logging

import requests
import backoff

from .defaults import Defaults
from .modules.url_validator import is_valid_url
from .modules.utils import backoff_handler_generic
from .exceptions import WebPageLoadError, ContentTypeError, InvalidURLError, RateLimitExceededError
from .custom_dataclasses import ScrapedResponse, WebscrapeConfig


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
        config: WebscrapeConfig = WebscrapeConfig
) -> ScrapedResponse:
    """
    Fetch DOM contents of a web page. SSRed HTML only, Cannot handle JS/CSR.

    Args:
        url: URL to scrape
        config: Webscraper Configuration of Class WebscrapeConfig
            # custom_headers: Custom HTTP headers to send with the request
            # params: URL parameters for the request
            # cookies: Cookies to send with the request
            # timeout: Request timeout in seconds
            # allow_redirects: Whether to follow redirects
            # verify_ssl: Whether to verify SSL certificates
            # expected_content_type: Expected content type (e.g., 'text/html')
            # proxy: Proxy configuration dict (e.g., {'http': 'http://proxy.com:8080'})
            # rate_limiter: Optional rate limiter object

    Returns:
        ScrapedResponse: Object containing the response and metadata

    Raises:
        InvalidURLError: If the URL is not valid
        WebPageLoadError: If there was an error loading the web page
        ContentTypeError: If the content type doesn't match expected type
    """
    start_time = time.time()
    error_message = None

    if config.rate_limiter:
        config.rate_limiter.wait()

    # Validate URL
    if not is_valid_url(url):
        raise InvalidURLError(f"Invalid URL format: {url}")

    # Set up headers
    headers = config.custom_headers or Defaults.DEFAULT_HTTP_HEADERS

    try:
        with requests.Session() as session:
            response = session.get(
                url,
                headers=headers,
                params=config.params,
                cookies=config.cookies,
                timeout=config.timeout,
                allow_redirects=config.allow_redirects,
                verify=config.verify_ssl,
                proxies=config.proxy
            )

            # Raise for HTTP errors
            response.raise_for_status()

            # Check content type if expected type is provided
            if config.expected_content_type and config.expected_content_type not in response.headers.get('Content-Type', ''):
                raise ContentTypeError(
                    f"Expected content type '{config.expected_content_type}' but got "
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
