import logging
from logging import FileHandler, Formatter


def get_logger_settings():
    """Retorn logging settings."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = FileHandler(filename="etl_log.txt")
    handler.setFormatter(
        Formatter(
            fmt="[%(asctime)s: %(levelname)s] Message: [%(message)s], "
            "(optional)Response: %(response)s"
        )
    )
    logger.addHandler(handler)

    return logger
