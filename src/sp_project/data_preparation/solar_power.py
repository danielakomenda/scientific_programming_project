import numpy as np
import pandas as pd


def total_solarpower_below_clouds(data, lat):
    """Calculates the relative daily solar-power above clouds
    at a given date and geographical latitude;

    lat: latitude in degrees
    date: pandas.DatetimeIndex
    """

    day_of_year = data.index.day_of_year

    delta = 23.45 * np.pi / 180 * np.sin(2 * np.pi / 365 * (284 + np.array(day_of_year)))[:, None]
    psi = lat * np.pi / 180
    H = np.linspace(-np.pi, np.pi, 48, endpoint=False)

    sin_theta = np.sin(delta) * np.sin(psi) + np.cos(delta) * np.cos(psi) * np.cos(H)

    power_above_clouds = pd.Series(
        index=data.index,
        data=np.maximum(0, sin_theta).mean(1),
    )

    power_above_clouds *= np.pi  # normalize to 1 at equator

    power_below_clouds = power_above_clouds * (100 - data.clouds) / 100

    return power_below_clouds
