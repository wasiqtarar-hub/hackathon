import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import g, request


def configure_logger(log_path="debug.log", name="genai_starter"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        Path(log_path),
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def register_request_logging(app, logger):
    @app.before_request
    def start_timer():
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_response(response):
        started_at = getattr(g, "request_started_at", None)
        duration_ms = (
            round((time.perf_counter() - started_at) * 1000, 2)
            if started_at is not None
            else 0
        )
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        logger.info(
            "%s %s -> %s in %sms | ip=%s",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
            client_ip,
        )
        return response
