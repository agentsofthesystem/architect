import logging
import sys

logging.basicConfig(
    datefmt="%m/%d/%Y %I:%M:%S %p", stream=sys.stdout, level=logging.NOTSET
)

logger = logging.getLogger()
