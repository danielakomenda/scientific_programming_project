import datetime
import asyncio
import pickle

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import pandas as pd
import numpy as np

from sp_project.app_state import AppState
from sp_project.data_collection.openweather_api_client import OpenWeatherClient


async def check_data_in_DB(collection, lon, lat):
    """Check if DB has already an entry to a specific location that is older than 24 hours;
    return the result, that is either None if there is no entry in the DB or the entry itself"""
    
    yesterday = datetime.datetime.now().astimezone() - datetime.timedelta(hours=24)
    
    result = await collection.find_one(
        {'location': {'$near' :{
            '$geometry' : dict(type="Point", coordinates=[lon, lat]),
            '$maxDistance' : 1000,
        }},
         'current.dt': {'$gt': yesterday}   
        }
    )

    return result


async def get_datapoint_from_OW(location):
    """Collect the data from a specific location from the OpenWeatherAPI;
    Return the data as a list with dictionaries"""
    
    data = await location.prediction()
    lat = data.pop('lat')
    lon = data.pop('lon')
    
    data['location'] = dict(type="Point", coordinates=[lon, lat])

    return data


async def insert_data_in_DB(collection, data:list[dict]):
    """Insert the data to the collection; if there is already a data-set with the same location, 
    the old data is overwritten"""
    
    for d in data:
        await collection.replace_one(
            dict(location ={'$near': {
                '$geometry': d['location'],
                '$maxDistance': 1000,
            }}),
            d,
            upsert=True,
        )


async def get_prediction_for_location(app_state: AppState, *, lon, lat):
    """Run all the above methodes and return the result"""
    collection = app_state.db_client.weatherprediction
    weather_station = app_state.ow_client.station_at(lon=lon, lat=lat)

    result = await check_data_in_DB(collection, lon=weather_station.lon, lat=weather_station.lat)
                
    if result is None:
        result = await get_datapoint_from_OW(weather_station)
        await insert_data_in_DB(collection, [result])
    
    return result

