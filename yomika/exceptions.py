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
