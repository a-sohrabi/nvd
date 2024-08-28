import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Optional, List

import aiofiles
import pytz
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from .database import vulnerability_collection
from .kafka_producer import producer
from .logger import LogManager
from .schemas import VulnerabilityResponse, VulnerabilityCreate

logger = LogManager('crud.py')

tehran_tz = pytz.timezone('Asia/Tehran')

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


async def bulk_create_or_update_vulnerabilities(vulnerabilities: List[VulnerabilityCreate]):
    global stats
    operations = []
    created_vulnerabilities = []
    updated_vulnerabilities = []

    for vulnerability in vulnerabilities:
        operations.append(
            UpdateOne(
                {"cve_id": vulnerability.cve_id},
                {"$set": vulnerability.dict()},
                upsert=True
            )
        )

    if operations:
        try:
            result = await vulnerability_collection.bulk_write(operations)

            matched_count = result.matched_count
            upserted_count = len(result.upserted_ids)

            for i, vulnerability in enumerate(vulnerabilities):
                if i in result.upserted_ids:
                    created_vulnerabilities.append(vulnerability)
                else:
                    updated_vulnerabilities.append(vulnerability)

            stats['inserted'] += upserted_count
            stats['updated'] += matched_count

            for vuln in created_vulnerabilities:
                producer.add_message('nvd.extract.created', key=str(vuln.cve_id), value=vuln.json())

            for vuln in updated_vulnerabilities:
                producer.add_message('nvd.extract.updated', key=str(vuln.cve_id), value=vuln.json())

            producer.flush()

        except BulkWriteError as bwe:
            logger.error(f"Bulk write error: {bwe.details}")
            stats['error'] += 1
        except Exception as e:
            logger.error(f"General error during bulk write: {str(e)}")
            stats['error'] += 1


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
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logger.error(e)
                result = None
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

            start_time_dt = datetime.fromtimestamp(start_time, tz=pytz.utc).astimezone(tehran_tz)

            stats["last_called"] = start_time_dt.strftime('%Y-%m-%d %H:%M:%S')
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
