import logging
import sys


def configure_logging() -> None:
    """
    Configure les logs de l'application.

    Les logs sont envoyés vers stdout afin d'être récupérés
    par Docker et les outils de supervision.
    """
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)