import logging
from .pubmed import Fetch


def log(debug):
    logger = logging.getLogger(__name__)
    if not debug:
        logger.disabled = True
    else:
        logger.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',  datefmt='%d/%m/%Y %H:%M')
        console_handler.setFormatter(formatter)

        if not logger.hasHandlers():
            logger.addHandler(console_handler)

        logger.info("Starting logging ...........")


def fetch(q, force_article=False, count=None):
    return Fetch(q, force_article, count)
