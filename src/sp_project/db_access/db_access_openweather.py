import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
collection = db.openweather


async def extract_heatingdemand(collection) -> pd.DataFrame:
    """Extract the daily average of the negative deviation of 14°C = 288°K"""
    pipeline = [
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
        }
    ]

    results=[]
    async for x in collection.aggregate(pipeline):
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    df["total"] = df.sum(axis="columns")
    
    return df


async def extract_avgtemp(collection) -> pd.DataFrame:
    """Extract the daily average, maximum and minimum of the temperature"""
    pipeline = [
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
    ]

    results=[]
    async for x in collection.aggregate(pipeline):
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    df["total"] = df.sum(axis="columns")
    
    return df


async def extract_windpower(collection) -> pd.DataFrame:
    """Extract the daily average of wind-speed**2, which is the equivalent of wind-power"""
    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$dt', 0, 10
                    ]
                }
            }
        }, {
            '$project': {
                'wind_speed': {
                    '$cond': {
                        'if': {
                            '$gt': [
                                '$wind_speed', 900
                            ]
                        }, 
                        'then': 0, 
                        'else': {
                            '$pow': [
                                '$wind_speed', 2
                            ]
                        }
                    }
                }, 
                'date': True
            }
        }, {
            '$group': {
                '_id': '$date', 
                'windpower': {
                    '$avg': '$wind_speed'
                }
            }
        }
    ]

    results=[]
    async for x in collection.aggregate(pipeline):
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    df["total"] = df.sum(axis="columns")
    
    return df