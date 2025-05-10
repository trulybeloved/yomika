import time
import asyncio

from ..defaults import Defaults

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

    async def wait_async(self):
        """Wait if necessary to respect the rate limit"""
        current_time = time.time()
        elapsed_since_last = current_time - self.last_request_time

        if elapsed_since_last < self.min_interval:
            sleep_time = self.min_interval - elapsed_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()