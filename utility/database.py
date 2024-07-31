from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings

client = AsyncIOMotorClient(settings.DATABASE_URL)
database = client[settings.DATABASE_NAME]
vulnerability_collection = database.get_collection("nvd")
# vulnerability_collection.create_index('cve_id', unique=True)
