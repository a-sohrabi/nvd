import time
from functools import wraps
from pathlib import Path
from typing import Optional

import aiofiles
from pydantic_core._pydantic_core import ValidationError
from pymongo.errors import BulkWriteError

from .config import settings
from .database import vulnerability_collection
from .kafka_producer import producer
from .logger import logger
from .schemas import VulnerabilityResponse, VulnerabilityCreate

stats = {
    "inserted": 0,
    "updated": 0,
    "errors": 0,
    "last_called": None,
    "durations": None
}


async def get_vulnerability(cve_id: str) -> Optional[VulnerabilityResponse]:
    document = await vulnerability_collection.find_one({"cve_id": cve_id})
    if document:
        return VulnerabilityResponse(**document)


async def create_or_update_vulnerability(vulnerability: VulnerabilityCreate):
    global stats
    result = None
    try:
        result = await vulnerability_collection.update_one(
            {"cve_id": vulnerability.cve_id},
            {"$set": vulnerability.dict()},
            upsert=True
        )
        if result.upserted_id:
            stats['inserted'] += 1
        else:
            stats['updated'] += 1

        try:
            producer.send(settings.KAFKA_TOPIC, key=str(vulnerability.cve_id), value=vulnerability.json())
            producer.flush()
        except Exception as ke:
            logger.error(f"Producing error {ke}")
            stats['error'] += 1
    except ValidationError as e:
        logger.error(f"Validation error for vulnerability {vulnerability.cve_id}: {e}")
        stats['error'] += 1
    except BulkWriteError as bwe:
        logger.error(f"Bulk write error for vulnerability {vulnerability.cve_id}: {bwe.details}")
        stats['error'] += 1
    except Exception as e:
        logger.error(f"Error updating/creating vulnerability {vulnerability.cve_id}: {e}")
        stats['error'] += 1

    return result


async def reset_stats():
    global stats
    stats = {
        "inserted": 0,
        "updated": 0,
        "errors": 0,
        "last_called": None,
        "durations": None
    }


async def get_stats():
    return stats


def record_stats():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            # Determine appropriate time unit
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)

            human_readable_duration = (
                f"{hours:.2f} hours" if hours >= 1 else
                f"{minutes:.2f} minutes" if minutes >= 1 else
                f"{seconds:.2f} seconds"
            )

            stats["last_called"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
            stats["durations"] = human_readable_duration

            return result

        return wrapper

    return decorator


async def read_version_file(version_file_path: Path) -> str:
    async with aiofiles.open(version_file_path, 'r') as file:
        version = await file.read()
    return version.strip()


async def read_markdown_file(markdown_file_path: Path) -> str:
    async with aiofiles.open(markdown_file_path, 'r') as file:
        content = await file.read()
    return content
