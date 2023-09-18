from __future__ import annotations

import logging

from hypernewsviewer.app import app as application


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return "kube-probe" not in msg or '"GET / HTTP/1.1" 200' not in msg


# Remove health check from application server logs
logging.getLogger("gunicorn.access").addFilter(HealthCheckFilter())

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    application.run()
