import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
collection = db.openweather


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
                'temp_C': {
                    '$avg': '$temp'
                }, 
                'min_temp_C': {
                    '$min': '$temp'
                }, 
                'max_temp_C': {
                    '$max': '$temp'
                }, 
                'uvi': {
                    '$avg': '$uvi'
                }, 
                'wind_kmh': {
                    '$avg': '$wind_speed'
                }, 
                'cloud_percent': {
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
    
    return df


async def extract_heatingdemand(collection=collection) -> pd.DataFrame:
    """Extract the daily average of the negative deviation of 14°C = 288°K"""
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


async def extract_windpower(collection=collection) -> pd.DataFrame:
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
            '$group': {
                '_id': '$date', 
                'windpower': {
                    '$avg': {
                        '$pow': [
                            '$wind_speed', 2
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
    df["total"] = df.sum(axis="columns")
    
    return df