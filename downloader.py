import os

import requests

from error_handler import handle_exception
from logger import logger


def download_file(url: str, dest_path: str):
    try:
        os.makedirs('downloaded', exist_ok=True)
        response = requests.get(url)
        response.raise_for_status()
        with open(dest_path, 'wb') as file:
            file.write(response.content)
        logger.info(f"File downloaded: {dest_path}")
    except Exception as e:
        handle_exception(e)
