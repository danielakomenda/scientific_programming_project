import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
collection = db.wetter2


async def extract_data_daily(collection=collection) -> pd.DataFrame:
    """Extract the daily averages of all the interesting datapoints including hours of daylight"""
    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$dt', 0, 10
                    ]
                }, 
                'sunhours': {
                    '$dateDiff': {
                        'startDate': '$sunrise', 
                        'endDate': '$sunset', 
                        'unit': 'minute'
                    }
                }
            }
        }, {
            '$group': {
                '_id': '$date', 
                'sunhours': {
                    '$avg': '$sunhours'
                }, 
                'avg_temp': {
                    '$avg': '$temp'
                }, 
                'min_temp': {
                    '$min': '$temp'
                }, 
                'max_temp': {
                    '$max': '$temp'
                }, 
                'uvi': {
                    '$avg': '$uvi'
                }, 
                'wind_speed': {
                    '$avg': '$wind_speed'
                }, 
                'clouds': {
                    '$avg': '$clouds'
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
    df["temp"] -= 273
    df["min_temp"] -= 273
    df["max_temp"] -= 273
    
    return df


async def extract_heatingdemand(collection=collection) -> pd.DataFrame:
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


async def extract_windpower(collection=collection) -> pd.DataFrame:
    """Extract the daily average of wind-speed**2, which is the equivalent of wind-power"""
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
                            {
                                '$divide': [
                                    "$wind_kmh",3.6
                                ]
                            }, 2]
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