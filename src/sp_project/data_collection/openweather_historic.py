import datetime
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import pandas as pd
import tqdm  # for status-bar
import anyio  # for parallel-processes

from sp_project.data_collection.openweather_api_client import OpenWeatherClient


# Name: (lon, lat)
coordinates = {
    "grid00": (7.10, 46.22),
    "grid01": (7.66, 46.22),
    "grid02": (8.79, 46.22),
    "grid03": (6.53, 46.62),
    "grid04": (7.10, 46.62),
    "grid05": (7.66, 46.62),
    "grid06": (8.23, 46.62),
    "grid07": (8.79, 46.62),
    "grid08": (9.36, 46.62),
    "grid09": (9.92, 46.62),
    "grid10": (7.10, 47.02),
    "grid11": (7.66, 47.02),
    "grid12": (8.23, 47.02),
    "grid13": (8.79, 47.02),
    "grid14": (9.36, 47.02),
    "grid15": (7.10, 47.41),
    "grid16": (7.66, 47.41),
    "grid17": (8.23, 47.41),
    "grid18": (8.79, 47.41),
    "grid19": (9.36, 47.41),
}


async def get_datapoints_from_ow(location, dt):
    """Collects the data from a specific location and a specific time from the OpenWeatherAPI"""
    
    data = await location.historic(dt)
    out_data = []
    # flattens the data
    for d in data["data"]:
        for k, v in data.items():
            if k == "data":
                continue
            d[k] = v
        out_data.append(d)
    return out_data


async def check_data_in_db(collection, lon, lat, dt, timelimit: datetime.timedelta = datetime.timedelta(minutes=5)):
    """Checks if DB has already an entry to a specific location and datetime +/- 5 Minutes"""
    result = await collection.find_one(
            dict(
                lon=lon,
                lat=lat,
                dt={"$lte": dt+timelimit, "$gte": dt-timelimit},
            ),)
    if result is None:
        return False
    return True


async def insert_data_in_db(collection, data: list[dict]):
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


async def run_the_program(ow_client, collection, locations: dict[str, tuple[float, float]], start_time, end_time):
    timestamps_list = pd.date_range(pd.Timestamp(start_time).floor("2H"), end_time, freq="2H")
    counter = 0
    limit_reached = False
    total = len(locations)*len(timestamps_list)
    pbar = tqdm.tqdm(total=total)  # Progress-Bar
    send_stream, receive_stream = anyio.create_memory_object_stream()

    async def handle(receive_stream):
        nonlocal counter, limit_reached
        async with receive_stream:
            async for weather_station, timestamp in receive_stream:
                if limit_reached:
                    return
                if not await check_data_in_db(
                        collection,
                        lon=weather_station.lon,
                        lat=weather_station.lat,
                        dt=timestamp,
                ):
                    async with anyio.CancelScope(shield=True):
                        # ignores external cancellation e.g. when another task fails, as long as the current task is ok
                        try:
                            result = await get_datapoints_from_ow(weather_station, timestamp)
                        except Exception as ex:
                            limit_reached = True
                            print(f'OneCallAPI reached limit at {counter=} and {timestamp=}: {ex!r}')
                            return
                        await insert_data_in_db(collection, result)
                    counter += 1
                pbar.update()

    async with anyio.create_task_group() as task_group:
        for _ in range(20):
            task_group.start_soon(handle, receive_stream.clone())
        receive_stream.close()
        async with send_stream:
            for timestamp in reversed(timestamps_list):
                timestamp = timestamp.to_pydatetime()
                for loc_name, loc_coord in coordinates.items():
                    weather_station = ow_client.station_at(*loc_coord)
                    try:
                        await send_stream.send((weather_station, timestamp))
                    except (anyio.BrokenResourceError, anyio.ClosedResourceError):
                        break
    pbar.close()
    print(
        f'Fetched {len(coordinates)} Locations '
        f'and {len(timestamps_list)} Timepoints '
        f'and added {counter}/{total} Elements to Database '
    )


async def main():
    api_key_ow = "***REMOVED***"
    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"

    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    collection = db.openweather

    end_time = datetime.datetime.now().astimezone()
    start_time = end_time - datetime.timedelta(days=365)

    async with OpenWeatherClient(
        api_key=api_key_ow,
    ) as OWclient:
        await run_the_program(
            ow_client=OWclient,
            collection=collection,
            locations=coordinates,
            start_time=start_time,
            end_time=end_time,
        )


if __name__ == "__main__":
    asyncio.run(main())
