import logging
from src.utils.config import DEBUG_MODE


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    # handler = logging.FileHandler(f"{name}.log", mode='w')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s %(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
