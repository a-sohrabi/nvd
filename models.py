from datetime import date

from pydantic import BaseModel


class Vulnerability(BaseModel):
    cve_id: str
    description: str
    published_date: date
    feed_type: str

    class Config:
        from_attributes = True
