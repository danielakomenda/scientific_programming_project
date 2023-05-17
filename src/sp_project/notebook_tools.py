import contextlib
import os

from sp_project.data_collection.openweather_api_client import OpenWeatherClient
from sp_project.data_preparation.db_client import get_global_db_client

api_key_ow = os.environ["OPENWEATHER_API_TOKEN"]


@contextlib.asynccontextmanager
async def default_clients(**kw):
    db_client = get_global_db_client()
    async with OpenWeatherClient(
        api_key = api_key_ow,
        **kw,
    ) as OWclient:
        yield OWclient, db_client

