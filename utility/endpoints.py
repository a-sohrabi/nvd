import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks

from .config import settings
from .crud import create_or_update_vulnerability, reset_stats, get_stats
from .downloader import download_file
from .extractor import extract_zip
from .health_check import check_mongo, check_kafka, check_url, check_internet_connection, check_loki
from .parser import parse_json

router = APIRouter()


async def download_and_extract(url: str, zip_path: Path, extract_to: Path) -> Path:
    await reset_stats()
    await download_file(url, zip_path)
    await extract_zip(zip_path, extract_to)
    return extract_to / zip_path.stem


async def process_vulnerabilities(json_file_path: Path, feed_type: str):
    vulnerabilities = await parse_json(json_file_path, feed_type)
    tasks = [create_or_update_vulnerability(vuln) for vuln in vulnerabilities]
    await asyncio.gather(*tasks)


async def process_year(year: int):
    base_dir = Path(settings.FILES_BASE_DIR) / 'downloaded'
    url = f'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-{year}.json.zip'
    zip_path = base_dir / f'nvdcve-1.1-{year}.json.zip'
    extract_to = base_dir / 'extracted_files'

    json_file_path = await download_and_extract(url, zip_path, extract_to)
    await process_vulnerabilities(json_file_path, 'yearly')


async def update_vulnerabilities(feed_type: str):
    base_dir = Path(settings.FILES_BASE_DIR) / 'downloaded'
    extract_to = base_dir / 'extracted_files'

    if feed_type == 'yearly':
        current_year = datetime.now().year
        start_year = 2002
        tasks = [process_year(year) for year in range(current_year, start_year - 1, -1)]
        await asyncio.gather(*tasks)
    else:
        url = getattr(settings, f"NVD_{feed_type.upper()}_URL")
        zip_path = base_dir / f'nvdcve-1.1-{feed_type}.json.zip'
        json_file_path = await download_and_extract(url, zip_path, extract_to)
        await process_vulnerabilities(json_file_path, feed_type)


@router.post("/all")
async def update_all_vulnerabilities(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_vulnerabilities, "yearly")
    return {"message": 'Started updating all vulnerabilities in the background!'}


@router.post("/recent")
async def update_recent_and_modified_vulnerabilities(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_vulnerabilities, "recent")
    background_tasks.add_task(update_vulnerabilities, "modified")
    return {"message": 'Started updating recent and modified vulnerabilities in the background!'}


@router.get("/stats")
async def get_vulnerabilities_stats():
    return await get_stats()


@router.get("/health_check")
async def check_health():
    mongo_status = await check_mongo()
    kafka_status = await check_kafka()
    nvd_status = await check_url(settings.NVD_MODIFIED_URL)
    loki_status = await check_loki()
    internet_status = await check_internet_connection()

    return {
        "internet": "connected" if internet_status else "disconnected",
        "mongo": "connected" if mongo_status else "disconnected",
        "kafka": "connected" if kafka_status else "disconnected",
        "nvd_urls": "accessible" if nvd_status else "inaccessible",
        "loki": "accessible" if loki_status else "inaccessible"

    }
