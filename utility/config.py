import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv('DATABASE_URL')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME')
    NVD_MODIFIED_URL: str = os.getenv('NVD_MODIFIED_URL')
    NVD_RECENT_URL: str = os.getenv('NVD_RECENT_URL')
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVER')
    KAFKA_TOPIC: str = os.getenv('KAFKA_TOPIC')
    NVD_YEARLY_URL: str = 'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-2023.json.zip'
    FILES_BASE_DIR: str = 'data'
    LOKI_URL: str = os.getenv('LOKI_URL')

    class Config:
        env_file = "../.env"


settings = Settings()
