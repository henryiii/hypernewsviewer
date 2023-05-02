from __future__ import annotations

import os
import sys
import importlib

if not importlib.find_spec("hypernewsviewer"):
    sys.path.append("src")

workers = int(os.environ.get("GUNICORN_PROCESSES", "3"))
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

forwarded_allow_ips = "*"
secure_scheme_headers = {"X-Forwarded-Proto": "https"}

wsgi_app = "hypernewsviewer.app:application"
