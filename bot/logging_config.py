import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs"):
    os.makedirs(log_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f"trading_bot_{date_str}.log")

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    # suppress werkzeug HTTP request logs — they flood the log panel
    # with GET /api/logs every 5 seconds and hide the actual bot activity
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # avoid duplicate handlers if setup_logging is called more than once
    if not any(isinstance(h, logging.FileHandler) for h in root.handlers):
        root.addHandler(file_handler)

    return log_path
