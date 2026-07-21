import logging
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from utils.logger import ColorFormatter

class ColorFormatterTest(unittest.TestCase):
    def test_uses_exiled_log_colors(self):
        formatter = ColorFormatter()
        colors = {
            logging.DEBUG: "\033[32m",
            logging.INFO: "\033[36m",
            logging.WARNING: "\033[35m",
            logging.ERROR: "\033[31m",
        }

        for level, color in colors.items():
            with self.subTest(level=level):
                record = logging.LogRecord("test", level, "", 0, "message", (), None)
                self.assertEqual(formatter.format(record)[0:5], color)

if __name__ == "__main__":
    unittest.main()
