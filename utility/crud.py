from typing import List, Optional

from pydantic_core._pydantic_core import ValidationError
from pymongo.errors import BulkWriteError

from .config import settings
from .database import vulnerability_collection
from .kafka_producer import producer
from .logger import logger
from .schemas import VulnerabilityResponse


async def get_vulnerability(cve_id: str) -> Optional[VulnerabilityResponse]:
    document = await vulnerability_collection.find_one({"cve_id": cve_id})
    if document:
        return VulnerabilityResponse(**document)


async def create_or_update_vulnerability(vulnerability):
    result = None
    try:
        result = await vulnerability_collection.update_one(
            {"cve_id": vulnerability.cve_id},
            {"$set": vulnerability.dict()},
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"Inserted new vulnerability: {vulnerability.cve_id}")
        else:
            logger.info(f"Updated vulnerability: {vulnerability.cve_id}")

        try:
            producer.send(settings.KAFKA_TOPIC, key=str(vulnerability.cve_id), value=vulnerability.json())
            producer.flush()
        except Exception as ke:
            logger.error(f"Producing error {ke}")
    except ValidationError as e:
        logger.error(f"Validation error for vulnerability {vulnerability.cve_id}: {e}")
    except BulkWriteError as bwe:
        logger.error(f"Bulk write error for vulnerability {vulnerability.cve_id}: {bwe.details}")
    except Exception as e:
        logger.error(f"Error updating/creating vulnerability {vulnerability.cve_id}: {e}")

    return result


async def get_all_vulnerabilities() -> List[VulnerabilityResponse]:
    vulnerabilities = []
    cursor = vulnerability_collection.find({})
    async for document in cursor:
        vulnerabilities.append(VulnerabilityResponse(**document))
    return vulnerabilities


async def get_vulnerabilities_by_feed_type(feed_type: str) -> List[VulnerabilityResponse]:
    vulnerabilities = []
    cursor = vulnerability_collection.find({"feed_type": feed_type})
    async for document in cursor:
        vulnerabilities.append(VulnerabilityResponse(**document))
    return vulnerabilities
