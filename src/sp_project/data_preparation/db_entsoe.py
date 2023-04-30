import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from .db_client import get_global_db_client



db_field_projection = {
    'wind': '$Wind Onshore Generation', 
    'solar': '$Solar Generation', 
    'nuclear': '$Nuclear Generation', 
    'water_reservoir': '$Hydro Water Reservoir Generation', 
    'water_river': '$Hydro Run-of-river and poundage Generation', 
    'water_pump': '$Hydro Pumped Storage Generation',   
}


async def extract_energy_data_daily() -> pd.DataFrame:
    """Extract the daily average of all the data"""
    collection = get_global_db_client().entsoe
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
            **{k: {'$avg': v} for k, v in db_field_projection.items()},
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
    df["total"] = df.sum(axis="columns")

    return df


async def extract_energy_data_raw() -> pd.DataFrame:
    """Extract all the data"""
    collection = get_global_db_client().entsoe
    projection={
        '_id': False,
        'datetime': "$datetime",
        **db_field_projection,
    }

    results= await collection.find(projection=projection).to_list(None)
    
    df = pd.DataFrame(results)
    df = df.set_index("datetime")
    df = df.set_index(pd.to_datetime(df.index).tz_localize("UTC"))
    df = df.sort_index()
    df["total"] = df.sum(axis="columns")

    return df


