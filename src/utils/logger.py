import logging

from utils.config import get_config

config = get_config()

format = "[%(asctime)s] [%(levelname)s | %(name)s] %(message)s"

logging.basicConfig(
    level=logging.DEBUG if config.log_level == "DEBUG" else logging.INFO,
    format=format
)

Logger = logging.getLogger
