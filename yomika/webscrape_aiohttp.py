import time
from typing import Optional, Callable
import logging
import asyncio

import requests
import backoff
import aiohttp

from .defaults import Defaults
from .modules.url_validator import is_valid_url
from .modules.utils import backoff_handler_generic
from .exceptions import WebPageLoadError, ContentTypeError, InvalidURLError, RateLimitExceededError
from .classes import ScrapedResponse, WebscrapeConfig


@backoff.on_exception(
    backoff.expo,
    exception=(WebPageLoadError,
        requests.RequestException,
        RateLimitExceededError,
        ConnectionError),
    max_tries=Defaults.DEFAULT_MAX_RETRIES,
    max_time=Defaults.DEFAULT_MAX_TIME,
    on_backoff=backoff_handler_generic)
async def webscrape_aiohttp(
        url: str,
        config: WebscrapeConfig = WebscrapeConfig,
        session: Optional[aiohttp.ClientSession] = None,
        on_success: Callable = None,
        on_failure: Callable = None
) -> ScrapedResponse:
    """
    Asynchronously fetch DOM contents of a web page using aiohttp. SSRed HTML only, Cannot handle JS/CSR.

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
            # proxy: Proxy URL (e.g., 'http://proxy.com:8080')
            # rate_limiter: Optional rate limiter object
        session: Optional aiohttp ClientSession for connection pooling
        on_success: Callback function that will be called when the scrape succeeds
        on_failure: Callback function that will be called if the scrape fails

    Returns:
        ScrapedResponse: Object containing the response and metadata

    Raises:
        InvalidURLError: If the URL is not valid
        WebPageLoadError: If there was an error loading the web page
        ContentTypeError: If the content type doesn't match expected type
    """

    start_time = time.time()
    error_message = None

    # Validate URL
    if not is_valid_url(url):
        raise InvalidURLError(f"Invalid URL format: {url}")

    # Apply rate limiting if configured
    if config.rate_limiter:
        await config.rate_limiter.wait_async()

    # Set up headers
    headers = config.custom_headers or Defaults.DEFAULT_HTTP_HEADERS

    # Set up timeout
    timeout_obj = aiohttp.ClientTimeout(total=config.timeout)

    # Create a flag to determine if we need to close the session
    should_close_session = False

    def run_on_failure():
        if not on_failure:
            return
        try:
            on_failure(scrape_result)
        except Exception as e:
            logging.exception(f'An exception was encountered while running the on_failure callback: {e}')

    try:
        # Use provided session or create a new one
        if session is None:
            session = aiohttp.ClientSession(timeout=timeout_obj)
            should_close_session = True

        # Configure request settings
        request_kwargs = {
            'url': url,
            'headers': headers,
            'params': config.params,
            'cookies': config.cookies,
            'allow_redirects': config.allow_redirects,
            'ssl': config.verify_ssl if config.verify_ssl else False
        }

        # Add proxy if specified
        if config.proxy:
            request_kwargs['proxy'] = config.proxy

        async with session.get(**request_kwargs) as response:
            # Check for common rate limiting status codes
            if response.status in (429, 503):
                raise RateLimitExceededError(f"Rate limit exceeded: {response.status}")

            # Raise for HTTP errors
            response.raise_for_status()

            # Read the response content
            content = await response.read()
            text = await response.text()

            # Check content type if expected type is provided
            content_type = response.headers.get('Content-Type', '')
            if config.expected_content_type and config.expected_content_type not in content_type:
                raise ContentTypeError(
                    f"Expected content type '{config.expected_content_type}' but got '{content_type}'"
                )

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            scrape_result = ScrapedResponse(
                url=url,
                status_code=response.status,
                content=content,
                text=text,
                headers=dict(response.headers),
                elapsed_time=elapsed_time,
                content_type=content_type,
                success=True
            )

            # run the on success callaback,
            try:
                if on_success:
                    on_success(scrape_result)
            except Exception as e:
                logging.exception(f'An exception was encountered while running the on_sucess callback: {e}')

            return scrape_result

    except aiohttp.ClientConnectorError as e:
        error_message = f"Connection error for {url}: {str(e)}"
        logging.error(error_message)
        run_on_failure()
        raise WebPageLoadError(error_message)

    except asyncio.TimeoutError as e:
        error_message = f"Timeout error for {url}: {str(e)}"
        logging.error(error_message)
        run_on_failure()
        raise WebPageLoadError(error_message)

    except aiohttp.TooManyRedirects as e:
        error_message = f"Too many redirects for {url}: {str(e)}"
        logging.error(error_message)
        run_on_failure()
        raise WebPageLoadError(error_message)

    except aiohttp.ClientResponseError as e:
        error_message = f"HTTP error for {url}: {str(e)}"
        logging.error(error_message)
        run_on_failure()
        raise WebPageLoadError(error_message)

    except ContentTypeError as e:
        error_message = str(e)
        logging.error(error_message)
        run_on_failure()
        raise

    except Exception as e:
        error_message = f"Unexpected error while loading {url}: {str(e)}"
        logging.error(error_message)
        run_on_failure()
        raise WebPageLoadError(error_message)

    finally:
        # Close the session if we created it
        if should_close_session and session is not None:
            await session.close()

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


