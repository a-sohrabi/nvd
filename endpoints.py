from typing import List

from app.config import settings
from app.crud import create_vulnerability, get_vulnerability, get_all_vulnerabilities, get_vulnerabilities_by_feed_type
from app.downloader import download_file
from app.extractor import extract_zip
from app.parser import parse_json
from app.schemas import VulnerabilityResponse
from fastapi import APIRouter

router = APIRouter()


async def update_vulnerabilities(feed_type: str):
    url = getattr(settings, f"NVD_{feed_type.upper()}_URL")
    zip_path = f'nvdcve-1.1-{feed_type}.json.zip'
    extract_to = 'extracted_files'
    json_file_path = f'{extract_to}/nvdcve-1.1-{feed_type}.json'

    download_file(url, zip_path)
    extract_zip(zip_path, extract_to)
    vulnerabilities = parse_json(json_file_path, feed_type)

    for vulnerability in vulnerabilities:
        if not await get_vulnerability(vulnerability.cve_id):
            await create_vulnerability(vulnerability)


@router.post("/update-all-vulnerabilities", response_model=List[VulnerabilityResponse])
async def update_all_vulnerabilities():
    await update_vulnerabilities("yearly")
    return await get_all_vulnerabilities()


@router.post("/update-recent-and-modified", response_model=List[VulnerabilityResponse])
async def update_recent_and_modified_vulnerabilities():
    await update_vulnerabilities("recent")
    await update_vulnerabilities("modified")
    recent_vulnerabilities = await get_vulnerabilities_by_feed_type("recent")
    modified_vulnerabilities = await get_vulnerabilities_by_feed_type("modified")
    return recent_vulnerabilities + modified_vulnerabilities


@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_all_vulnerabilities_endpoint():
    return await get_all_vulnerabilities()
