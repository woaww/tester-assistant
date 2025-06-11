import logging
import sys
from src.text_constants import LOG_FORMAT, LOG_DATETIME_FORMAT

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format=LOG_FORMAT,
                    datefmt=LOG_DATETIME_FORMAT)
LOGGER = logging.getLogger(__name__)