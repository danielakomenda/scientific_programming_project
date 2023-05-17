import os

from bson.codec_options import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


_global_db_client = None


def get_global_db_client(uri: str | None = None):
    global _global_db_client

    if _global_db_client is not None:
        return _global_db_client

    uri = uri or os.environ['MONGODB_URI']
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    _global_db_client = DBclient.get_database("data", codec_options=CodecOptions(tz_aware=True))

    return _global_db_client
