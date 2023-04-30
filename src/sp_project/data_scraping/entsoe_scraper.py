import asyncio
import re # regular-expression
import json
import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import httpx
import bs4 # beautifulsoup
import pandas as pd
import tqdm
import anyio



async def get_datapoints_from_entsoe(country, date):
    """get-Request to the entsoe.eu-page to get all 'Generation per Type'-Data"""
    
    # There are 20 different productiontypes
    productiontypes = [
        ("productionType.values", f"B{k:02}")
        for k in range(1,20)
    ]

    async with httpx.AsyncClient(
        base_url="https://transparency.entsoe.eu",
    ) as client:
        res = await client.get(
            url="/generation/r2/actualGenerationPerProductionType/show",
            params=list({
                "areaType": "CTY",
                "viewType": "GRAPH",
                "dateTime.dateTime": f"{date:%d.%m.%Y} 00:00|UTC|DAYTIMERANGE",
                "dateTime.endDateTime": f"{date:%d.%m.%Y} 00:00|UTC|DAYTIMERANGE",
                "dateTime.timezone": "UTC",
                "area.values": f"CTY|{country}!CTY|{country}",
            }.items()) + productiontypes,
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    content_type = res.headers["content-type"].lower().split(";")
    content_params = {k.strip():v.strip() for k,v in (l.split("=") for l in content_type[1:])}
    content_type = content_type[0]
    
    if True:
        # make sure the content is UTF-8 and parse the content with bs4
        assert res.headers["content-type"] == "text/html;charset=UTF-8", res.headers["content-type"]
        soup = bs4.BeautifulSoup(res.content.decode("utf-8"))
    else:
        assert content_type == "text/html", res.headers["content-type"]
        soup = bs4.BeautifulSoup(res.content.decode(content_params["charset"]))

    # select only the part 'script' and the chart-list of the http-file
    javascript_str = soup.find("script").text
    match = re.search(r"var\s+chart\s*=\s*(\{.*\})\s*;", javascript_str, re.S)
    assert match is not None

    # returns the first element of the group
    data = json.loads(match.group(1))

    # defines the columns for the dataframe
    columns = {
        k:" ".join(v["title"].split())
        for k,v in
        data["graphDesign"].items()
    }

    df = pd.DataFrame(
        data["chartData"]
    ).set_index(data["categoryName"]).astype(float).rename(columns=columns)

    # combine time with date to get a real timestamp
    df = df.set_index(pd.MultiIndex.from_arrays(
        [
            [country]*df.shape[0],
            df.index.to_series().apply(
                lambda v: datetime.datetime.combine(date, datetime.time.fromisoformat(v))
            ).dt.tz_localize("UTC"),
        ],
        names=["country", "datetime"],
    ))
    return df


async def insert_data_in_DB(collection, data):
    data = data.reset_index().to_dict("records")
    for d in data:
        await collection.replace_one(
            dict(
                country=d["country"],
                datetime=d["datetime"],
            ),
            d,
            upsert=True,
        )


async def handle_run_the_program(receive_stream, collection):
    """Handels parallel-processes"""
    async with receive_stream:
        async for country, base_date in receive_stream:
            try:
                data = await get_datapoints_from_entsoe(country, base_date)
                await insert_data_in_DB(collection, data)

            except Exception as ex:
                print(f"{country} / {base_date:%y-%m-%d} failed: {ex!r}")
                raise


async def run_the_program(collection, country, start, end):
        
    send_stream, receive_stream = anyio.create_memory_object_stream()

    async with anyio.create_task_group() as task_group:
        
        for _ in range(20):
            task_group.start_soon(
                handle_run_the_program, 
                receive_stream.clone(),
                collection
            )
        receive_stream.close()
        
        async with send_stream:
            date_range = tqdm.tqdm(
                pd.date_range(start,end,freq="D"),
                leave=False,
            )

            for base_date in date_range:
                date_range.set_description(f"{base_date:%y-%m-%d}")
                await send_stream.send((country, base_date))


async def run_the_program_unparallel(collection, country, start, end):
    
    date_range = tqdm.tqdm(
        pd.date_range(start,end,freq="D"),
        leave=False,
    )
    
    for base_date in date_range:
        try:
            date_range.set_description(f"{base_date:%y-%m-%d}")
            data = await get_datapoints_from_entsoe(country, base_date)
            await insert_data_in_DB(collection, data)

        except Exception as ex:
            print(f"{country} / {base_date:%y-%m-%d} failed: {ex!r}")
            raise


def main():
    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    collection = db.entsoe
    
    country = "10YCH-SWISSGRIDZ"
    end_time = datetime.datetime.now().astimezone()
    start_time = end_time - datetime.timedelta(days=3)

    asyncio.run(run_the_program_unparallel(collection=collection, country=country, start=start_time, end=end_time))


if __name__ == "__main__":
    main()