import logging

from utils.config import get_config

config = get_config()

format = "[%(asctime)s] [%(levelname)s | %(name)s] %(message)s"

class ColorFormatter(logging.Formatter):
    colors = {
        logging.DEBUG: "\033[32m",
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[35m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[31m",
    }

    def __init__(self):
        super().__init__(format)

    def format(self, record):
        message = super().format(record)
        color = self.colors.get(record.levelno)
        return f"{color}{message}\033[0m" if color else message

logging.basicConfig(
    level=logging.DEBUG if config.log_level == "DEBUG" else logging.INFO,
    format=format
)
logging.getLogger("discord").propagate = False

Logger = logging.getLogger
