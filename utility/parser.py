import json
from datetime import datetime
from pathlib import Path
from typing import List

import aiofiles

from .logger import logger, log_error
from .schemas import VulnerabilityCreate


async def parse_json(json_path: Path, feed_type: str) -> List[VulnerabilityCreate]:
    try:
        async with aiofiles.open(json_path, "r") as json_file:
            data = json.loads(await json_file.read())

        vulnerabilities = []
        for item in data["CVE_Items"]:
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            cve = item["cve"]
            configurations = item["configurations"]
            impact = item["impact"]
            published_date_str = item["publishedDate"]
            last_modified_date_str = item["lastModifiedDate"]

            published_date = datetime.strptime(published_date_str, "%Y-%m-%dT%H:%MZ")
            last_modified_date = datetime.strptime(last_modified_date_str, "%Y-%m-%dT%H:%MZ")

            vulnerabilities.append(VulnerabilityCreate(
                cve_id=cve_id,
                cve=cve,
                configurations=configurations,
                impact=impact,
                published_date=published_date,
                last_modified_date=last_modified_date,
                feed_type=feed_type
            ))

        logger.info(f"JSON parsing completed for {feed_type} feed")
        return vulnerabilities
    except Exception as e:
        log_error(e, {'function': 'parse_json', 'context': 'parsing the json of vulnerabilities'})
