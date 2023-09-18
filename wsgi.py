from __future__ import annotations

import logging

from hypernewsviewer.app import app as application


class HealthCheckFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not ("kube-probe" in msg and '"GET / HTTP/1.1" 200' in msg)


# Remove health check from application server logs
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    application.run()
