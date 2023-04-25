import asyncio
import re # regular-expression
import json
import datetime

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import httpx
import bs4 # beautifulsoup
import pandas as pd



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
                "areaType": "BZN",
                "viewType": "GRAPH",
                "dateTime.dateTime": f"{date:%d.%m.%Y} 00:00|UTC|DAYTIMERANGE",
                "dateTime.endDateTime": f"{date:%d.%m.%Y} 00:00|UTC|DAYTIMERANGE",
                "dateTime.timezone": "UTC",
                "area.values": "CTY|10YCH-SWISSGRIDZ!BZN|10YCH-SWISSGRIDZ",
            }.items()) + productiontypes,
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    # make sure the content is UTF-8 and parse the content with bs4
    assert res.headers["content-type"] == "text/html;charset=UTF-8"
    soup = bs4.BeautifulSoup(res.content.decode("utf-8"))

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
            ["10YCH-SWISSGRIDZ!BZN"]*df.shape[0],
            df.index.to_series().apply(
                lambda v: datetime.datetime.combine(date, datetime.time.fromisoformat(v))
            ).dt.tz_localize("UTC"),
        ],
        names=["Country", "Datetime"],
    ))
    return df


async def insert_data_in_DB(collection, data):
    data = data.reset_index().to_dict("records")
    for d in data:
        await collection.replace_one(
            dict(
                Country=d["Country"],
                Datetime=d["Datetime"],
            ),
            d,
            upsert=True,
        )


async def db_update_with_new_data(country, date):
    uri = "mongodb+srv://scientificprogramming:***REMOVED***@scientificprogramming.nzfrli0.mongodb.net/test"
    DBclient = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
    db = DBclient.data
    energy_collection = db.energy
    counter = 0

    for i in range(5):
        dates = date - datetime.timedelta(days=i)
        data = await get_datapoints_from_entsoe(country, dates)
        await insert_data_in_DB(energy_collection, data)
        counter += 1
        print(counter)


def main():
    date = datetime.date(2023, 4, 11)
    country = "10YCH-SWISSGRIDZ!BZN"
    asyncio.run(db_update_with_new_data(country, date))


if __name__ == "__main__":
    main()