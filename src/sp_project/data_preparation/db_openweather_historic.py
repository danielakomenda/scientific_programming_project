import pandas as pd

from sp_project.app_state import AppState


async def extract_data_daily(app_state: AppState) -> pd.DataFrame:
    """Extract the daily averages of all the interesting datapoints including hours of daylight"""
    
    collection = app_state.db_client.openweather

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
                }, 
                'temp': {
                    '$cond': [
                        {
                            '$gte': [
                                '$temp', 200
                            ]
                        }, '$temp', {
                            '$add': [
                                '$temp', 10000
                            ]
                        }
                    ]
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
                }, 
                'rain': {
                    '$push': '$rain'
                }, 
                'snow': {
                    '$push': '$snow'
                }
            }
        }
    ]

    results = []
    async for x in collection.aggregate(pipeline):
        total_rain = 0
        total_snow = 0

        for r in x['rain']:
            for k, v in r.items():
                rain = v
                hours = int(k.strip('h'))
                total_rain += (rain*hours)
        avg_rain = total_rain/24
        x['rain'] = avg_rain

        for s in x['snow']:
            for k, v in s.items():
                snow = v
                hours = int(k.strip('h'))
                total_snow += (snow*hours)
        avg_snow = total_snow/24
        x['snow'] = avg_snow

        results.append(x)

    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
 
    df["avg_temp"] -= 273.15
    df["min_temp"] -= 273.15
    df["max_temp"] -= 273.15

    return df


async def extract_heatingdemand(app_state: AppState) -> pd.DataFrame:
    """Extract the daily average of the negative deviation of 14°C = 288°K"""
    
    collection = app_state.db_client.openweather

    pipeline = [
        {
            '$addFields': {
                'date': {
                    '$substr': [
                        '$dt', 0, 10
                    ]
                }, 
                'temp': {
                    '$cond': [
                        {
                            '$gte': [
                                '$temp', 200
                            ]
                        }, '$temp', {
                            '$add': [
                                '$temp', 10000
                            ]
                        }
                    ]
                }
            }
        }, {
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
            '$group': {
                '_id': '$date', 
                'heating_demand': {
                    '$avg': '$heatingdemand'
                }
            }
        }
    ]

    results = []
    async for x in collection.aggregate(pipeline):
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    
    return df


async def extract_windpower(app_state: AppState) -> pd.DataFrame:
    """Extract the daily average of wind-speed**2, which is the equivalent of wind-power"""
    
    collection = app_state.db_client.openweather
    
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
                            '$wind_speed', 3
                        ]
                    }
                }
            }
        }
    ]

    results = []
    async for x in collection.aggregate(pipeline):
        results.append(x)
    
    df = pd.DataFrame(results)
    df = df.set_index("_id")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC").rename("date"))
    df = df.sort_index()
    
    return df
