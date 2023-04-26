import pandas as pd
import matplotlib.pyplot as plt
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import numpy as np
import sklearn.cross_decomposition


uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = DBclient.data
energy_collection = db.energy
weather_collection = db.weather


async def extract_windpower(collection):
    cursor = collection.aggregate([
    {
        '$addFields': {
            'date': {
                '$substr': [
                    '$dt', 0, 10 # Timezone UTC
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
    ])

    results=[]
    async for x in cursor:
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")

    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    
    return df


async def extract_heatingdemand(collection):
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

async def extract_energydata(collection):
    cursor = collection.aggregate([
    {
        '$addFields': {
            'date': {
                '$substr': [
                    '$Datetime', 0, 10
                ]
            }
        }
    }, {
        '$group': {
            '_id': '$date', 
            'wind': {
                '$avg': '$Wind Onshore Generation'
            }, 
            'solar': {
                '$avg': '$Solar Generation'
            }, 
            'nuclear': {
                '$avg': '$Nuclear Generation'
            }, 
            'water_reservoir': {
                '$avg': '$Hydro Water Reservoir Generation'
            }, 
            'water_river': {
                '$avg': '$Hydro Run-of-river and poundage Generation'
            }, 
            'water_pump': {
                '$avg': '$Hydro Pumped Storage Generation'
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
    df["total"] = df.sum(axis="columns")   
    return df