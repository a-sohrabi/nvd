from typing import List, Optional

import pymongo.errors

from database import vulnerability_collection
from logger import logger
from schemas import VulnerabilityResponse


async def get_vulnerability(cve_id: str) -> Optional[VulnerabilityResponse]:
    document = await vulnerability_collection.find_one({"cve_id": cve_id})
    if document:
        return VulnerabilityResponse(**document)


async def create_or_update_vulnerability(vulnerability):
    try:
        vulnerability_collection.create_index('cve_id', unique=True)
        result = await vulnerability_collection.update_one(
            {"cve_id": vulnerability.cve_id},
            {"$set": vulnerability.dict()},
            upsert=True
        )
        logger.info(f"Create or Update {vulnerability.cve_id}")
    except pymongo.errors.DuplicateKeyError as e:
        return 'duplicate key'
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
