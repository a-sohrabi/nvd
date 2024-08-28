from pathlib import Path

import aiofiles
import aiohttp
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from .logger import LogManager

logger = LogManager('downloader.py')


@retry(wait=wait_exponential(multiplier=1, min=4, max=10),
       stop=stop_after_attempt(5),
       retry=retry_if_exception_type(aiohttp.ClientError))
async def download_file(url: str, dest: Path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                async with aiofiles.open(dest, 'wb') as f:
                    await f.write(content)
    except aiohttp.ClientError as e:
        logger.error(e)
