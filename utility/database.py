from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings

client = AsyncIOMotorClient(settings.DATABASE_URL)
database = client[settings.DATABASE_NAME]
vulnerability_collection = database.get_collection("nvd")


async def ensure_collection_exists():
    await vulnerability_collection.insert_one({"_id": "dummy_id"})
    await vulnerability_collection.delete_one({"_id": "dummy_id"})


async def create_indexes():
    await ensure_collection_exists()

    await vulnerability_collection.create_index("cve_id", unique=True)
