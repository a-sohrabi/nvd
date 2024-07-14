from typing import List, Optional

from database import vulnerability_collection
from schemas import VulnerabilityCreate, VulnerabilityResponse


async def get_vulnerability(cve_id: str) -> Optional[VulnerabilityResponse]:
    document = await vulnerability_collection.find_one({"cve_id": cve_id})
    if document:
        return VulnerabilityResponse(**document)


async def create_vulnerability(vulnerability: VulnerabilityCreate) -> VulnerabilityResponse:
    result = await vulnerability_collection.insert_one(vulnerability.dict())
    vulnerability.id = str(result.inserted_id)
    return vulnerability


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
