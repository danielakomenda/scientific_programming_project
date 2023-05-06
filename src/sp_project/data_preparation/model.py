import pandas as pd
import matplotlib.pyplot as plt
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import numpy as np
import sklearn.cross_decomposition


def total_daily_solarpower(date, lat):
    """Calculates the relative daily solar-power above clouds
    at a given date and geographical latitude;

    lat: latitude in degrees
    date: pandas.DatetimeIndex
    """

    delta = 23.45 * np.pi / 180 * np.sin(2 * np.pi / 365 * (284 + date.dayofyear.values))[:, None]
    psi = lat * np.pi / 180
    H = np.linspace(-np.pi, np.pi, 48, endpoint=False)

    sin_theta = np.sin(delta) * np.sin(psi) + np.cos(delta) * np.cos(psi) * np.cos(H)

    power_above_clouds = pd.Series(
        index=date,
        data=np.maximum(0, sin_theta).mean(1),
    )

    return power_above_clouds * np.pi  # normalize to 1 at equator


def prepare_prediction_features(raw_data, lat):
    input_features = pd.DataFrame(dict(
        heating_demand=np.maximum(0, raw_data.temperature - 14),
        windpower=raw_data.wind_speed ** 2,
        rain=raw_data.rain,
        solar_power=total_daily_solarpower(
            raw_data.index,
            lat
        ) * (100 - raw_data.clouds) / 100,
    ))

    return input_features


def energy_prediction(model, input_features):
    prediction = model["regressor"].predict(input_features.loc[:, model["input_columns"]])
    prediction = pd.DataFrame(prediction, index=input_features.index, columns=model["prediction_columns"])

    return prediction

