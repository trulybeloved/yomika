import logging

def backoff_handler_generic(details):
    """Log backoff retry attempts."""
    logging.warning(
        f"Backing off {details['wait']:.1f} seconds after {details['tries']} tries "
        f"calling function {details['target'].__name__} with args {details['args']} "
        f"and kwargs {details['kwargs']}"
    )