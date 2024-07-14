import json
from datetime import datetime
from typing import List
from schemas import VulnerabilityCreate
from logger import logger
from error_handler import handle_exception

def parse_json(json_path: str, feed_type: str) -> List[VulnerabilityCreate]:
    try:
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)

        vulnerabilities = []
        for item in data['CVE_Items']:
            cve_id = item['cve']['CVE_data_meta']['ID']
            description = item['cve']['description']['description_data'][0]['value']
            published_date = datetime.strptime(item['publishedDate'], '%Y-%m-%dT%H:%M:%S.%fZ').date()

            vulnerabilities.append(VulnerabilityCreate(
                cve_id=cve_id,
                description=description,
                published_date=published_date,
                feed_type=feed_type
            ))
        logger.info(f"JSON parsing completed for {feed_type} feed")
        return vulnerabilities
    except Exception as e:
        handle_exception(e)
