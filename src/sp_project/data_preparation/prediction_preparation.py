import pandas as pd
import numpy as np


from sp_project.data_collection.openweather_prediction import get_prediction_for_location
from sp_project.data_preparation.solar_power import total_solarpower_below_clouds
from sp_project.app_state import AppState


def extract_predictions_daily(app_state: AppState, *, lon, lat):
    openweather_response = await get_prediction_for_location(app_state, lon=lon, lat=lat)

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


def prepare_prediction_features(data, lat):
    input_features = pd.DataFrame(dict(
        heating_demand=np.maximum(0, data.temperature - 14),
        windpower=data.wind_speed ** 2,
        rain=data.rain,
        solar_power=total_solarpower_below_clouds(
            data.index,
            lat
        )
    ))

    return input_features


def energy_prediction(model, input_features):
    prediction = model["regressor"].predict(input_features.loc[:, model["input_columns"]])
    prediction = pd.DataFrame(prediction, index=input_features.index, columns=model["prediction_columns"])

    return prediction
