import logging
from datetime import datetime
from pathlib import Path

from .db import Log, get_db

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "logs.txt"


class DBHandler(logging.Handler):
    def emit(self, record):
        try:
            db = get_db()
            log_in_db = Log(timestamp=datetime.fromtimestamp(record.created), level=record.levelname, message=self.format(record))
            db.add(log_in_db)
            db.commit()
        except Exception as e:
            print(f"Error logging to DB: {e}")
        finally:
            db.close()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    file_handler = logging.FileHandler(LOG_FILE)
    console_handler = logging.StreamHandler()
    db_handler = DBHandler()
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler.setLevel(logging.WARNING)
        console_handler.setLevel(logging.INFO)
        db_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter("[%(asctime)s] | %(levelname)-7s | %(name)s %(funcName)s() | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(db_handler)
        logger.addHandler(file_handler)
        logger.propagate = False
    return logger
