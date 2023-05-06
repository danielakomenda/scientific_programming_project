import pandas as pd

from .db_client import get_global_db_client



async def extract_data_daily() -> pd.DataFrame:
    """Extract the daily averages of all the interesting datapoints"""
    
    collection = get_global_db_client().wetter2
    
    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$datetime', 0, 10
                    ]
                }
            }
        }, 
        {
            '$group': {
                '_id': '$date', 
                'avg_temp': {
                    '$avg': '$temp_C'
                }, 
                'min_temp': {
                    '$min': '$temp_C'
                }, 
                'max_temp': {
                    '$max': '$temp_C'
                }, 
                'rain': {
                    '$avg': '$rain_mm'
                }, 
                'wind_speed': {
                    '$avg': '$wind_kmh'
                }, 
                'clouds': {
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
    df["wind_speed"] /= 3.6
    
    return df


async def extract_heatingdemand() -> pd.DataFrame:
    """Extract the daily average of the negative deviation of 14°C = 288°K"""
    
    collection = get_global_db_client().wetter2
    
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
                'heating_demand': {
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


async def extract_windpower() -> pd.DataFrame:
    """Extract the daily average of wind-speed**2, which is the equivalent of wind-power"""
    
    collection = get_global_db_client().wetter2
    
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