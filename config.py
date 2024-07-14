from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "nvd"
    NVD_MODIFIED_URL: str = 'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.zip'
    NVD_RECENT_URL: str = 'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.zip'
    NVD_YEARLY_URL: str = 'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2023.json.zip'

    class Config:
        env_file = ".env"


settings = Settings()
