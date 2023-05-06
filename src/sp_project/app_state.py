import dataclasses

import motor.motor_asyncio

from sp_project.data_collection.openweather_api_client import OpenWeatherClient


@dataclasses.dataclass
class AppState:
    ow_client: OpenWeatherClient
    db_client: motor.motor_asyncio.AsyncIOMotorDatabase
    model: dict
