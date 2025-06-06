from dataclasses import dataclass

@dataclass
class Defaults:
        _instance = None

        def __new__(cls, *args, **kwargs):
                """This class method ensures that only one instance of the class exists"""
                if cls._instance is None:
                        cls._instance = super(Defaults, cls).__new__(cls)
                return cls._instance

        DEFAULT_HTTP_HEADERS = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }

        DEFAULT_REQ_TIMEOUT = 30
        DEFAULT_RPS_LIMIT = 250

        # backoff-retry
        DEFAULT_MAX_RETRIES = 3
        DEFAULT_MAX_TIME = 90