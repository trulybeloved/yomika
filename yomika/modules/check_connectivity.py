import socket
import logging
import urllib.request
import requests
import time
import sys
from typing import List, Dict, Union, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("connectivity_checker")

# Default configuration - can be modified as needed
DEFAULT_CONFIG = {
    "timeout": 5,  # seconds
    "retry_count": 2,
    "retry_delay": 1,  # seconds
    "reliable_hosts": [
        "1.1.1.1",  # Cloudflare DNS
        "8.8.8.8",  # Google DNS
        "208.67.222.222",  # OpenDNS
    ],
    "http_endpoints": [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://www.amazon.com"
    ],
    "dns_hosts": [
        "google.com",
        "cloudflare.com",
        "microsoft.com"
    ],
    "socket_port": 53,  # DNS port
}


class InternetConnectivityChecker:
    """Class to check internet connectivity using multiple methods."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the connectivity checker with configuration.

        Args:
            config: Optional custom configuration dictionary
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        self.timeout = self.config["timeout"]
        self.retry_count = self.config["retry_count"]
        self.retry_delay = self.config["retry_delay"]
        self.session = requests.Session()

    def _check_socket_connection(self, host: str) -> Tuple[str, bool, str]:
        """
        Check connectivity using a socket connection.

        Args:
            host: Host to connect to

        Returns:
            Tuple of (host, success status, error message if any)
        """
        for attempt in range(self.retry_count + 1):
            try:
                socket.create_connection(
                    (host, self.config["socket_port"]),
                    timeout=self.timeout
                )
                return host, True, ""
            except (socket.timeout, socket.error) as e:
                error_msg = str(e)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    continue
                return host, False, error_msg

    def _check_dns_resolution(self, hostname: str) -> Tuple[str, bool, str]:
        """
        Check if DNS resolution works for a hostname.

        Args:
            hostname: Hostname to resolve

        Returns:
            Tuple of (hostname, success status, error message if any)
        """
        for attempt in range(self.retry_count + 1):
            try:
                socket.gethostbyname(hostname)
                return hostname, True, ""
            except socket.gaierror as e:
                error_msg = str(e)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    continue
                return hostname, False, error_msg

    def _check_http_connection(self, url: str) -> Tuple[str, bool, str]:
        """
        Check connectivity by making an HTTP request.

        Args:
            url: URL to request

        Returns:
            Tuple of (url, success status, error message if any)
        """
        for attempt in range(self.retry_count + 1):
            try:
                response = self.session.head(url, timeout=self.timeout)
                response.raise_for_status()
                return url, True, ""
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    continue
                return url, False, error_msg

    def _check_urllib_connection(self) -> Tuple[bool, str]:
        """
        Check connectivity using urllib as a fallback.

        Returns:
            Tuple of (success status, error message if any)
        """
        for attempt in range(self.retry_count + 1):
            try:
                urllib.request.urlopen("https://www.google.com", timeout=self.timeout)
                return True, ""
            except urllib.error.URLError as e:
                error_msg = str(e)
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)
                    continue
                return False, error_msg

    def is_connected(self, verbose: bool = False) -> bool:
        """
        Check if the device has internet connectivity using multiple methods.

        Args:
            verbose: If True, log detailed results of each check

        Returns:
            Boolean indicating if connectivity is available
        """
        checks = []
        results = {"socket": [], "dns": [], "http": []}

        # Parallel check of socket connections
        with ThreadPoolExecutor(max_workers=min(4, len(self.config["reliable_hosts"]))) as executor:
            futures = [executor.submit(self._check_socket_connection, host)
                       for host in self.config["reliable_hosts"]]

            for future in as_completed(futures):
                host, success, error = future.result()
                results["socket"].append((host, success, error))
                if success:
                    checks.append(True)
                elif verbose:
                    logger.debug(f"Socket connection to {host} failed: {error}")

        # If socket connections all failed, try DNS resolution
        if not any(checks):
            with ThreadPoolExecutor(max_workers=min(4, len(self.config["dns_hosts"]))) as executor:
                futures = [executor.submit(self._check_dns_resolution, host)
                           for host in self.config["dns_hosts"]]

                for future in as_completed(futures):
                    host, success, error = future.result()
                    results["dns"].append((host, success, error))
                    if success:
                        checks.append(True)
                    elif verbose:
                        logger.debug(f"DNS resolution for {host} failed: {error}")

        # If still no connections, try HTTP
        if not any(checks):
            with ThreadPoolExecutor(max_workers=min(4, len(self.config["http_endpoints"]))) as executor:
                futures = [executor.submit(self._check_http_connection, url)
                           for url in self.config["http_endpoints"]]

                for future in as_completed(futures):
                    url, success, error = future.result()
                    results["http"].append((url, success, error))
                    if success:
                        checks.append(True)
                    elif verbose:
                        logger.debug(f"HTTP connection to {url} failed: {error}")

        # Last resort, try urllib
        if not any(checks):
            success, error = self._check_urllib_connection()
            if success:
                checks.append(True)
            elif verbose:
                logger.debug(f"Urllib connection failed: {error}")

        if verbose:
            self._print_results(results)

        return any(checks)

    def _print_results(self, results: Dict) -> None:
        """
        Print detailed results of connectivity checks.

        Args:
            results: Dictionary containing check results
        """
        logger.info("=== Connectivity Check Results ===")

        for check_type, checks in results.items():
            if checks:
                logger.info(f"\n{check_type.upper()} Checks:")
                for host, success, error in checks:
                    status = "SUCCESS" if success else "FAILED"
                    logger.info(f"  {host}: {status}")
                    if not success:
                        logger.debug(f"    Error: {error}")

    def get_connection_details(self) -> Dict:
        """
        Get detailed information about internet connectivity.

        Returns:
            Dictionary with connectivity information
        """
        results = {
            "connected": False,
            "socket_checks": [],
            "dns_checks": [],
            "http_checks": []
        }

        # Check socket connections
        for host in self.config["reliable_hosts"]:
            host, success, error = self._check_socket_connection(host)
            results["socket_checks"].append({
                "host": host,
                "success": success,
                "error": error if not success else ""
            })
            if success:
                results["connected"] = True

        # Check DNS resolutions if needed
        if not results["connected"]:
            for host in self.config["dns_hosts"]:
                host, success, error = self._check_dns_resolution(host)
                results["dns_checks"].append({
                    "host": host,
                    "success": success,
                    "error": error if not success else ""
                })
                if success:
                    results["connected"] = True

        # Check HTTP connections if needed
        if not results["connected"]:
            for url in self.config["http_endpoints"]:
                url, success, error = self._check_http_connection(url)
                results["http_checks"].append({
                    "url": url,
                    "success": success,
                    "error": error if not success else ""
                })
                if success:
                    results["connected"] = True

        return results


def is_connected(timeout: int = 5, verbose: bool = False) -> bool:
    """
    Simple function to check internet connectivity.

    Args:
        timeout: Connection timeout in seconds
        verbose: If True, print detailed information

    Returns:
        Boolean indicating if internet is available
    """
    checker = InternetConnectivityChecker({"timeout": timeout})
    return checker.is_connected(verbose)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check internet connectivity")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed results")
    parser.add_argument("--timeout", "-t", type=int, default=5, help="Connection timeout in seconds")
    parser.add_argument("--details", "-d", action="store_true", help="Show detailed connection information")

    args = parser.parse_args()

    if args.details:
        checker = InternetConnectivityChecker({"timeout": args.timeout})
        details = checker.get_connection_details()
        print(f"Internet connected: {details['connected']}")
        print("\nSocket checks:")
        for check in details["socket_checks"]:
            print(f"  {check['host']}: {'Success' if check['success'] else 'Failed - ' + check['error']}")

        if details["dns_checks"]:
            print("\nDNS checks:")
            for check in details["dns_checks"]:
                print(f"  {check['host']}: {'Success' if check['success'] else 'Failed - ' + check['error']}")

        if details["http_checks"]:
            print("\nHTTP checks:")
            for check in details["http_checks"]:
                print(f"  {check.get('url', '')}: {'Success' if check['success'] else 'Failed - ' + check['error']}")
    else:
        connected = is_connected(timeout=args.timeout, verbose=args.verbose)
        print(f"Internet connected: {connected}")