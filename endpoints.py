from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks

from config import settings
from crud import create_or_update_vulnerability, get_all_vulnerabilities
from downloader import download_file
from extractor import extract_zip
from parser import parse_json
from schemas import VulnerabilityResponse

router = APIRouter()


async def update_vulnerabilities(feed_type: str):
    url, zip_path, extract_to, json_file_path = '', '', 'extracted_files', ''
    if feed_type == 'yearly':
        current_year = datetime.now().year
        start_year = 2002
        for year in range(current_year, start_year - 1, -1):
            url = f'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.zip'
            zip_path = f'downloaded/nvdcve-1.1-{year}.json.zip'
            json_filename = f'nvdcve-1.1-{year}.json'
            json_file_path = f'{extract_to}/{json_filename}'
            download_file(url, zip_path)
            extract_zip(zip_path, extract_to)
            vulnerabilities = parse_json(json_file_path, feed_type)
            for vulnerability in vulnerabilities:
                await create_or_update_vulnerability(vulnerability)

    else:
        url = getattr(settings, f"NVD_{feed_type.upper()}_URL")
        zip_path = f'downloaded/nvdcve-1.1-{feed_type}.json.zip'
        json_file_path = f'{extract_to}/nvdcve-1.1-{feed_type}.json'

        download_file(url, zip_path)
        extract_zip(zip_path, extract_to)
        vulnerabilities = parse_json(json_file_path, feed_type)

        for vulnerability in vulnerabilities:
            await create_or_update_vulnerability(vulnerability)


@router.post("/all")
async def update_all_vulnerabilities(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_vulnerabilities, "yearly")
    return 'Started updating all vulnerabilities in the background!'


@router.post("/recent")
async def update_recent_and_modified_vulnerabilities(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_vulnerabilities, "recent")
    background_tasks.add_task(update_vulnerabilities, "modified")
    return 'Started updating recent and modified vulnerabilities in the background!'


@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def get_all_vulnerabilities_endpoint():
    return await get_all_vulnerabilities()
