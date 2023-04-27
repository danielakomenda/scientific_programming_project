import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
collection = db.wetter2


async def extract_heatingdemand(collection=db.wetter2) -> pd.DataFrame:
    """Extract the daily average of the negative deviation of 14°C = 288°K"""
    pipeline = [
        {
            '$addFields': {
                'heatingdemand': {
                    '$cond': {
                        'if': {
                            '$lte': [
                                '$temp_C', 14
                            ]
                        }, 
                        'then': {
                            '$subtract': [
                                14, '$temp_C'
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
                        '$datetime', 0, 10
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
    
    return df


async def extract_data_daily(collection=db.wetter2) -> pd.DataFrame:
    """Extract the daily averages of all the interesting datapoints"""
    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$datetime', 0, 10
                    ]
                }
            }
        }, {
            '$group': {
                '_id': '$date', 
                'temp_C': {
                    '$avg': '$temp_C'
                }, 
                'min_temp_C': {
                    '$min': '$temp_C'
                }, 
                'max_temp_C': {
                    '$max': '$temp_C'
                }, 
                'rain_mm': {
                    '$avg': '$rain_mm'
                }, 
                'wind_kmh': {
                    '$avg': '$wind_kmh'
                }, 
                'cloud_percent': {
                    '$avg': '$cloud_percent'
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
    
    return df


async def extract_windpower(collection=db.wetter2) -> pd.DataFrame:
    """Extract the wind-speed**2, which is the equivalent of wind-power"""
    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$datetime', 0, 10
                    ]
                }
            }
        }, {
            '$group': {
                '_id': '$date', 
                'windpower': {
                    '$avg': {
                        '$pow': [
                            '$wind_kmh', 2
                        ]
                    }
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
    
    return df