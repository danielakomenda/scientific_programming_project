import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
collection = db.weather


async def extract_heatingdemand(collection):
    """Extract the negative deviation of 14°C = 288°K"""
    cursor = collection.aggregate([
    {
        '$addFields': {
            'heatingdemand': {
                '$cond': {
                    'if': {
                        '$lte': [
                            '$temp', 288
                        ]
                    }, 
                    'then': {
                        '$subtract': [
                            288, '$temp'
                        ]
                    }, 
                    'else': 0
                }
            }
        }
    }, {
        '$addFields': {
            'date': {
                '$substr': [
                    '$dt', 0, 10
                ]
            }
        }
    }, {
        '$group': {
            '_id': '$date', 
            'avg_demand': {
                '$avg': '$heatingdemand'
            }
        }
    }, {
        '$match': {
            'avg_demand': {
                '$gt': 0
            }
        }
    }
    ])

    results=[]
    async for x in cursor:
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")

    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    
    return df


async def extract_avgtemp(collection):
    cursor = collection.aggregate([
    {
        '$addFields': {
            'date': {
                '$substr': [
                    '$dt', 0, 10
                ]
            }
        }
    }, {
        '$group': {
            '_id': '$date', 
            'avg_temp': {
                '$avg': '$temp'
            },
            'min_temp': {
                '$min': '$temp'
            },
            'max_temp': {
                '$max': '$temp'
            }
        }
    }
    ])

    results=[]
    async for x in cursor:
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")

    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    
    return df