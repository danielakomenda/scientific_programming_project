from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


_global_db_client = None


def get_global_db_client():
    global _global_db_client

    if _global_db_client is not None:
        return _global_db_client

    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    _global_db_client = DBclient.data

    return _global_db_client
