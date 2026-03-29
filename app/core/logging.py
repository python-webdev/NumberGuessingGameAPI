import json
import logging
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if hasattr(record, "extra_data"):
            log_data.update(getattr(record, "extra_data", {}))

        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger


logger = setup_logging()
