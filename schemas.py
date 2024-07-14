from pydantic import BaseModel
from typing import List
from datetime import date

class VulnerabilityBase(BaseModel):
    cve_id: str
    description: str
    published_date: date
    feed_type: str

class VulnerabilityCreate(VulnerabilityBase):
    pass

class VulnerabilityResponse(VulnerabilityBase):
    id: str

    class Config:
        orm_mode = True
