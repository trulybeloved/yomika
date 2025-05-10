import logging
import re
from urllib.parse import urlparse
from typing import Union, Dict, Optional, Literal, LiteralString


class URLValidator:
    """
    A class for validating URLs with configurable options.

    This validator checks:
    - URL structure and format
    - Presence of required components
    - Protocol limitations
    - Domain validation
    - Length restrictions
    """

    # Regular expression for domain validation
    # Follows RFC 1034/1035 with some practical limitations
    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]$'
    )

    # Regular expression for IP address validation (IPv4)
    IPV4_PATTERN = re.compile(
        r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    )

    # Regular expression for IPv6 validation (simplified)
    IPV6_PATTERN = re.compile(
        r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|'
        r'^::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}$|'
        r'^[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}$|'
        r'^[0-9a-fA-F]{1,4}:[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4}$|'
        r'^(?:[0-9a-fA-F]{1,4}:){0,2}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,3}[0-9a-fA-F]{1,4}$|'
        r'^(?:[0-9a-fA-F]{1,4}:){0,3}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:){0,2}[0-9a-fA-F]{1,4}$|'
        r'^(?:[0-9a-fA-F]{1,4}:){0,4}[0-9a-fA-F]{1,4}::(?:[0-9a-fA-F]{1,4}:)?[0-9a-fA-F]{1,4}$|'
        r'^(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}::[0-9a-fA-F]{1,4}$|'
        r'^(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}::$'
    )

    def __init__(self,
                 allowed_schemes: list = None,
                 require_tld: bool = True,
                 require_query: bool = False,
                 allow_ip: bool = True,
                 allow_ipv6: bool = True,
                 min_length: int = 3,
                 max_length: int = 2083  # IE's max URL length
                 ):
        """
        Initialize the URL validator with configurable options.

        Args:
            allowed_schemes: List of allowed URL schemes/protocols (e.g., ['http', 'https'])
                            If None, all schemes are allowed
            require_tld: Whether URLs must have a top-level domain
            require_query: Whether URLs must have a query string
            allow_ip: Whether IP addresses are allowed as hosts
            allow_ipv6: Whether IPv6 addresses are allowed as hosts
            min_length: Minimum length of the URL
            max_length: Maximum length of the URL
        """
        self.allowed_schemes = allowed_schemes
        self.require_tld = require_tld
        self.require_query = require_query
        self.allow_ip = allow_ip
        self.allow_ipv6 = allow_ipv6
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, url: str) -> Union[bool, Dict[str, str]]:
        """
        Validate a URL string.

        Args:
            url: The URL string to validate

        Returns:
            bool: True if valid, or a dictionary with error details if invalid
        """
        # Check if URL is None or empty
        if not url or not isinstance(url, str):
            return {"error": "URL must be a non-empty string"}

        # Check URL length
        if len(url) < self.min_length:
            return {"error": f"URL is too short (minimum {self.min_length} characters)"}

        if len(url) > self.max_length:
            return {"error": f"URL is too long (maximum {self.max_length} characters)"}

        # Try to parse the URL
        try:
            parsed_url = urlparse(url)

            # Check scheme
            if not parsed_url.scheme:
                return {"error": "URL must include a scheme (e.g., 'http://', 'https://')"}

            if self.allowed_schemes and parsed_url.scheme not in self.allowed_schemes:
                return {
                    "error": f"URL scheme '{parsed_url.scheme}' is not allowed. Allowed schemes: {', '.join(self.allowed_schemes)}"}

            # Check netloc (domain/host)
            if not parsed_url.netloc:
                return {"error": "URL must include a domain/host"}

            # Handle IP addresses
            is_ipv4 = self.IPV4_PATTERN.match(parsed_url.hostname)
            is_ipv6 = self.IPV6_PATTERN.match(parsed_url.hostname) if parsed_url.hostname else False

            if is_ipv4 and not self.allow_ip:
                return {"error": "IP addresses are not allowed as hosts"}

            if is_ipv6 and not self.allow_ipv6:
                return {"error": "IPv6 addresses are not allowed as hosts"}

            # If it's not an IP address, validate the domain
            if not is_ipv4 and not is_ipv6:
                # Check TLD if required
                if self.require_tld and (not '.' in parsed_url.netloc or parsed_url.netloc.endswith('.')):
                    return {"error": "URL must have a valid top-level domain"}

                # Check domain format
                if not self._is_valid_domain(parsed_url.hostname):
                    return {"error": "URL contains an invalid domain name"}

            # Check query string if required
            if self.require_query and not parsed_url.query:
                return {"error": "URL must include a query string"}

            return True

        except Exception as e:
            return {"error": f"Invalid URL format: {str(e)}"}

    def _is_valid_domain(self, domain: Optional[str]) -> bool:
        """
        Check if a domain name is valid.

        Args:
            domain: The domain name to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not domain:
            return False

        # Check domain length
        if len(domain) > 253:
            return False

        return bool(self.DOMAIN_PATTERN.match(domain))


def is_valid_url(url: str,
                 allowed_schemes: list = None,
                 strict: bool = False,
                 validator: Literal['urllib', 'self'] = 'urllib') -> bool:
    """
    A simple function to validate URLs with common settings.

    Args:
        url: The URL string to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
        strict: If True, applies stricter validation rules

    Returns:
        bool: True if the URL is valid, False otherwise
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    if validator == 'self':

        validator = URLValidator(
            allowed_schemes=allowed_schemes,
            require_tld=strict,
            require_query=False,
            allow_ip=not strict,
            allow_ipv6=not strict
        )

        result = validator.validate(url)

        if not result is True:
            print(result)

        return result is True

    else:
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception as e:
            logging.error(f'URL Validation failed: {e}')
            return False


if __name__ == "__main__":
    print(is_valid_url("https://www.example.com"))  # True
    print(is_valid_url("invalid-url"))  # False

    custom_validator = URLValidator(
        allowed_schemes=['https'],
        require_tld=True,
        allow_ip=False
    )

    urls_to_check = [
        "https://www.example.com",
        "http://insecure-example.com",
        "https://192.168.1.1",
        "https://example",
        "ftp://files.example.com"
    ]

    for url in urls_to_check:
        result = custom_validator.validate(url)
        if result is True:
            print(f"{url} is valid")
        else:
            print(f"{url} is invalid: {result['error']}")