import datetime
import asyncio
from turtle import up, update

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import pandas as pd

from sp_project.weather.openweather_api_client import OpenWeatherClient


api_key_ow = """***REMOVED***""".strip()

coordinates = {
    "zurich": (47.38, 8.54),# "47.38°N 8.54°E",
    "basel": (47.56, 7.59),
}



def main():
    end_time = datetime.datetime.now().astimezone()
    start_time = end_time - datetime.timedelta(hours=48)
    asyncio.run(db_update_with_new_data(coordinates, start_time, end_time))



async def get_datapoints_from_OW(location, dt):
    """Collects the data from a specific location and a specific time from the OpenWeatherAPI"""
    data = await location.historic(dt)
    out_data = []
    # flattens the data
    for d in data["data"]:
        for k, v in data.items():
            if k=="data":
                continue
            d[k] = v
        out_data.append(d)
    return out_data

async def check_data_in_DB(collection, lon, lat, dt, timelimit:datetime.timedelta=datetime.timedelta(minutes=5)):
    """Checks if DB has already an entry to a specific location and datetime +/- 5 Minutes"""
    result = await collection.find_one(
            dict(
                lon=lon,
                lat=lat,
                dt={"$lte":dt+timelimit, "$gte":dt-timelimit},
            ),)
    if result is None:
        return False
    return True



async def insert_data_in_DB(collection, data:list[dict]):
    for d in data:
        await collection.replace_one(
            dict(
                lon=d["lon"],
                lat=d["lat"],
                dt=d["dt"],
            ),
            d,
            upsert=True,
        )

async def db_update_with_new_data(location, start_time, end_time):
    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    weather_collection = db.weather

    timestamps_list = pd.date_range(pd.Timestamp(start_time).floor("H"), end_time, freq="H")

    counter = 0

    async with OpenWeatherClient(
        api_key = api_key_ow,
    ) as OWclient:
        for loc_name, loc_coord in coordinates.items():
            location = OWclient.station_at(*loc_coord)
            for timestamp in timestamps_list:
                timestamp = timestamp.to_pydatetime()
                if await check_data_in_DB(weather_collection, lon=location.lon, lat=location.lat, dt=timestamp):
                    continue
                await insert_data_in_DB(weather_collection, await get_datapoints_from_OW(location, timestamp))
                counter+=1
    print(f'Fetched {len(coordinates)} Locations and {len(timestamps_list)} Timepoints and added {counter}/{len(coordinates)*len(timestamps_list)} Elements to Database ') 

if __name__ == "__main__":
    main()
    