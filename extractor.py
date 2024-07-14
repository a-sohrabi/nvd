import zipfile

from error_handler import handle_exception
from logger import logger


def extract_zip(zip_path: str, extract_to: str):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info(f"File extracted to: {extract_to}")
    except Exception as e:
        handle_exception(e)
