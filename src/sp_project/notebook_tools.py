import contextlib
import os
from pathlib import Path

import yaml

from sp_project.data_collection.openweather_api_client import OpenWeatherClient
from sp_project.db_client import get_global_db_client

credentials_file = Path(__file__).parents[2] / "credentials.yaml"

@contextlib.asynccontextmanager
async def default_clients(**kw):
    if credentials_file.exists():
        with credentials_file.open("rt") as fh:
            credentials = yaml.safe_load(fh)
    else:
        credentials = os.environ
    db_client = get_global_db_client(uri=credentials["MONGODB_URI"])
    async with OpenWeatherClient(
        api_key=credentials["OPENWEATHER_API_TOKEN"],
        **kw,
    ) as OWclient:
        yield OWclient, db_client

