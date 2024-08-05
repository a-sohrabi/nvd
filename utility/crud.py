from typing import List, Optional

from pydantic_core._pydantic_core import ValidationError
from pymongo.errors import BulkWriteError

from .config import settings
from .database import vulnerability_collection
from .kafka_producer import producer
from .logger import logger
from .schemas import VulnerabilityResponse

stats = {
    "inserted": 0,
    "updated": 0,
    "errors": 0
}


async def get_vulnerability(cve_id: str) -> Optional[VulnerabilityResponse]:
    document = await vulnerability_collection.find_one({"cve_id": cve_id})
    if document:
        return VulnerabilityResponse(**document)


async def create_or_update_vulnerability(vulnerability):
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
        "errors": 0
    }


async def get_stats():
    return stats
