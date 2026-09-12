"""Logging Configuration

Provides structured and colorized console logging for microservice pipeline operations.
"""

import logging
import sys

def setup_logging():
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Quiet down chatty libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.ERROR)
    logging.getLogger("google_genai.models").setLevel(logging.ERROR)

logger = logging.getLogger("cleandesk")
