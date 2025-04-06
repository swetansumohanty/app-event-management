import logging
import sys

# custom logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)  

# print logs to the console
console_handler = logging.StreamHandler(sys.stderr)  
console_handler.setLevel(logging.DEBUG)  

# formatter to format the log messages
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)
