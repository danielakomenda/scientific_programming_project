import datetime
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import pandas as pd

from sp_project.data_scraping.openweather_api_client import OpenWeatherClient



api_key_ow = """***REMOVED***""".strip()
lon = 8.23
lat = 46.62


async def check_data_in_DB(collection, lon, lat):
    """Checks if DB has already an entry to a specific location that is older than 24 hours"""
    
    yesterday = datetime.datetime.now().astimezone() - datetime.timedelta(hours=24)
    
    result = await collection.find_one(
        {'location': {'$near' :{
            '$geometry' : dict(type="Point", coordinates=[lon, lat]),
            '$maxDistance' : 1000,
        }},
         'current.dt': {'$gt': yesterday}   
        }
    )
    if result is None:
        return False
    return True


async def get_datapoints_from_OW(location):
    """Collects the data from a specific location and a specific time from the OpenWeatherAPI"""
    
    data = await location.prediction()
    lat = data.pop('lat') # drop the lat from the data, but saves it in the variable lat
    lon = data.pop('lon') # drop the lon from the data, but saves it in the variable lon
    
    data['location'] = dict(type="Point", coordinates=[lon, lat]) 
    # create a new geo-sphere-variable 'location with lon and lat

    out_data = [data]

    return out_data


async def insert_data_in_DB(collection, data:list[dict]):
    """Insert the data to the collection; if there is already a data-set with the same location, 
    the new data overwrites the old data"""
    
    for d in data:
        await collection.replace_one(
            dict(location ={'$near' :{
                '$geometry' : d['location'],
                '$maxDistance' : 1000,
            }}),
            d,
            upsert=True,
        )


async def run_the_program(collection, lon, lat):
    """Run all the above methodes and return 'True' if data is written in the DB 
    and return 'False' if there is no new data"""
    
    async with OpenWeatherClient(
        api_key = api_key_ow,
    ) as OWclient:       
        location = OWclient.prediction_station_at(lon=lon, lat=lat)
        if not await check_data_in_DB(collection, lon=location.lon, lat=location.lat):
            result = await get_datapoints_from_OW(location)
            await insert_data_in_DB(collection, result)  
            return True
    
    return False


def main():
    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    collection = db.weatherprediction

    lon = lon
    lat = lat

    asyncio.run(run_the_program(collection, lon=lon, lat=lat))


if __name__ == "__main__":
    main()