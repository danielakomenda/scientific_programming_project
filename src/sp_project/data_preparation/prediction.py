import pandas as pd

import sp_project.data_collection.openweather_prediction as weatherprediction
from sp_project.app_state import AppState


def extract_predictions_daily(openweather_response):
    rows = []
    for d in openweather_response["daily"]:
        dt = pd.Timestamp(d["dt"])
        rows.append(dict(
            dt=dt,
            temperature=d["temp"]["day"]-273.15,
            wind_speed=d["wind_speed"],
            rain=d.get("rain", 0),
            clouds=d.get("clouds", 0),
        )),
    return pd.DataFrame(rows).set_index("dt")


async def fetch_prediction_daily(app_state: AppState, *, lon, lat):
    openweather_response = await weatherprediction.get_prediction_for_location(app_state, lon=lon, lat=lat)
    result = extract_predictions_daily(openweather_response)

    return result
