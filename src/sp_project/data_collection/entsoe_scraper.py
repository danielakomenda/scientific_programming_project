import asyncio
import re  # regular-expression
import json
import datetime
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import httpx
import bs4  # beautifulsoup
import pandas as pd
import tqdm



async def get_datapoints_from_entsoe(country, date):
    """Access the website with the needed parameters; 
    select the interesting data from the json-document and create a pandas-dataFrame;
    return a pandas-dataFrame with the location-, time- and weather-data"""
    
    # There are 20 different productiontypes
    productiontypes = [
        ("productionType.values", f"B{k:02}")
        for k in range(1, 21)
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

    # make sure the content is UTF-8 and parse the content with bs4
    assert res.headers["content-type"] == "text/html;charset=UTF-8", res.headers["content-type"]
    soup = bs4.BeautifulSoup(res.content.decode("utf-8"))

    # select only the part 'script' and the chart-list of the http-file
    javascript_str = soup.find("script").text
    match = re.search(r"var\s+chart\s*=\s*({.*})\s*;", javascript_str, re.S)
    assert match is not None

    # returns the first element of the group
    data = json.loads(match.group(1))

    # defines the columns for the dataframe
    columns = {
        k: " ".join(v["title"].split())
        for k, v in
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


async def insert_data_in_db(collection, data):
    """Insert the data to the collection; if there is already a data-set with the same location and time, 
    the old data is overwritten"""

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


async def run_the_program(collection, country, start_date, end_date):
    """Run all the above methodes"""
    
    date_range = tqdm.tqdm(
        pd.date_range(start_date, end_date, freq="D"),
        leave=False,
    )
    
    for base_date in date_range:
        try:
            date_range.set_description(f"{base_date:%y-%m-%d}")
            data = await get_datapoints_from_entsoe(country, base_date)
            await insert_data_in_db(collection, data)

        except Exception as ex:
            print(f"{country} / {base_date:%y-%m-%d} failed: {ex!r}")
            raise


def main():
    uri = os.environ['MONGODB_URI']
    db_client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = db_client.data
    collection = db.entsoe
    
    country = "10YCH-SWISSGRIDZ"
    end_date = datetime.datetime.now().astimezone()
    start_date = end_date - datetime.timedelta(days=365)

    asyncio.run(run_the_program(collection=collection, country=country, start_date=start_date, end_date=end_date))


if __name__ == "__main__":
    main()
