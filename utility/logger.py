import json
import logging
import os

import httpx
from pythonjsonlogger import jsonlogger


class LokiHandler(logging.Handler):
    def __init__(self, url, tags=None):
        super().__init__()
        self.url = url
        self.tags = tags or {}

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.send_log(log_entry, record)
        except Exception as e:
            print(f"An error occurred in emit: {e}")

    def send_log(self, log_entry, record):
        headers = {'Content-Type': 'application/json'}
        payload = {
            "streams": [
                {
                    "stream": self.tags,
                    "values": [[str(int(record.created * 1e9)), log_entry]]
                }
            ]
        }
        try:
            # Disable logging temporarily to avoid recursion
            logging.getLogger("httpx").disabled = True
            response = httpx.post(self.url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.text}")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            # Re-enable logging
            logging.getLogger("httpx").disabled = False


def setup_logging(loki_url, app_name):
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')

    loki_handler = LokiHandler(
        url=loki_url,
        tags={"application": app_name}
    )
    loki_handler.setLevel(logging.INFO)
    loki_handler.setFormatter(formatter)

    logger_ = logging.getLogger()
    logger_.setLevel(logging.INFO)
    logger_.handlers = []  # Clear existing handlers
    logger_.addHandler(loki_handler)
    return logger_


loki_url = os.getenv("LOKI_URL")
app_name = "nvd_scrapper"
logger = setup_logging(loki_url, app_name)
