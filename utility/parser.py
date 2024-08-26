import json
from datetime import datetime
from pathlib import Path
from typing import List, AsyncGenerator

import aiofiles

from .logger import logger
from .schemas import VulnerabilityCreate


async def parse_json_in_batches(json_path: Path, feed_type: str, batch_size: int = 1000) -> AsyncGenerator[
    List[VulnerabilityCreate], None]:
    try:
        async with aiofiles.open(json_path, "r") as json_file:
            data = json.loads(await json_file.read())

        batch = []
        for item in data["CVE_Items"]:
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            cve = item["cve"]
            configurations = item["configurations"]
            impact = item["impact"]
            published_date_str = item["publishedDate"]
            last_modified_date_str = item["lastModifiedDate"]

            published_date = datetime.strptime(published_date_str, "%Y-%m-%dT%H:%MZ")
            last_modified_date = datetime.strptime(last_modified_date_str, "%Y-%m-%dT%H:%MZ")

            vulnerability = VulnerabilityCreate(
                cve_id=cve_id,
                cve=cve,
                configurations=configurations,
                impact=impact,
                published_date=published_date,
                last_modified_date=last_modified_date,
                feed_type=feed_type
            )

            batch.append(vulnerability)

            # If batch is full, yield it and start a new batch
            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield the remaining items in the batch
        if batch:
            yield batch

        logger.info(f"JSON parsing completed for {feed_type} feed")
    except Exception as e:
        logger.error(e)
