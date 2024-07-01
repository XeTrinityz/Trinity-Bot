from logging.config import dictConfig
import logging
import os

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(levelname)s] [%(module)s/%(name)s] ➭ %(message)s",
            "datefmt": "%d/%m/%Y %I:%M:%S %p",
        },
        "standard": {
            "format": "[%(levelname)s] ➭ %(name)s | %(message)s",
            "datefmt": "%d/%m/%Y %I:%M:%S %p",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/info.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


dictConfig(LOGGING_CONFIG)