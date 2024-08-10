import asyncio
from datetime import datetime
from pathlib import Path

import markdown2
from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse

from .config import settings
from .crud import create_or_update_vulnerability, reset_stats, get_stats, record_stats, read_version_file, \
    read_markdown_file, get_vulnerability
from .downloader import download_file
from .extractor import extract_zip
from .health_check import check_mongo, check_kafka, check_url, check_internet_connection, check_loki
from .logger import logger
from .parser import parse_json

router = APIRouter()

VERSION_FILE_PATH = Path(__file__).parent.parent / 'version.txt'
README_FILE_PATH = Path(__file__).parent.parent / 'README.md'


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


@record_stats()
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


@router.get("/all")
async def update_all_vulnerabilities(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_vulnerabilities, "yearly")
    return {"message": 'Started updating all vulnerabilities in the background!'}


@router.get("/recent")
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


@router.get("/version")
async def get_version():
    try:
        version = await read_version_file(VERSION_FILE_PATH)
        return {"version": version}
    except FileNotFoundError as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)


@router.get("/readme", response_class=HTMLResponse)
async def get_readme():
    try:
        content = await read_markdown_file(README_FILE_PATH)
        html_content = markdown2.markdown(content)
        return HTMLResponse(content=html_content, headers={"Content-Type": "text/markdown; charset=utf-8"},
                            status_code=200)
    except FileNotFoundError as e:
        logger.error(e)
    except Exception as e:
        logger.error(e)


@router.get('/detail/{cve_id}')
async def get_detail(cve_id: str):
    cve = await get_vulnerability(cve_id)
    if not cve:
        return JSONResponse(status_code=404, content={"message": f'{cve_id} not found'})
    return cve
