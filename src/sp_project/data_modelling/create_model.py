import pandas as pd
import sklearn.cross_decomposition
import sklearn.linear_model

import sp_project.data_preparation.db_entsoe as entsoe_data
import sp_project.data_preparation.db_wetter2 as wetter2_data
from sp_project.data_preparation.solar_power import total_solarpower_below_clouds


async def prepare_input_features_daily():
    daily_data = await wetter2_data.extract_data_daily()
    heating_demand = await wetter2_data.extract_heatingdemand()
    windpower = await wetter2_data.extract_windpower()
    solar_power = total_solarpower_below_clouds(daily_data, 47)

    input_features = [heating_demand, windpower, daily_data.rain, solar_power.rename("solar_power")]
    input_features = pd.concat(input_features, axis="columns")
    return input_features


async def prepare_target_features_daily():
    return await entsoe_data.extract_energy_data_daily()


async def prepare_input_features_weekly():
    input_daily = await prepare_input_features_daily()
    return pd.concat(input_daily, axis="columns").resample('W').mean()


async def prepare_target_features_weekly():
    target_features = await entsoe_data.extract_energy_data_daily()
    return target_features.resample('W').mean()


async def pls_regression_weekly():
    input_features_weekly = await prepare_input_features_weekly()
    target_features_weekly = await prepare_target_features_weekly()

    valid_input_features_weekly = input_features_weekly.dropna(axis="index", how='any').index
    valid_target_features_weekly = target_features_weekly.dropna(axis="index", how='any').index

    joined_index = valid_input_features_weekly.intersection(valid_target_features_weekly)
    joined_index = joined_index[joined_index.year == 2021]  # fit model in 2021 and verify in 2022

    pls2 = sklearn.cross_decomposition.PLSRegression(n_components=2)

    return pls2.fit(
        input_features_weekly.loc[joined_index, :],
        target_features_weekly.loc[joined_index, :],
    )


def calculate_prediction_coefficients(model, input_features, target_features):
    return pd.DataFrame(
        data=model.coef_,
        index=input_features.columns,
        columns=target_features.columns,
    ).T


def calculate_x_weights(model, input_features):
    return pd.DataFrame(index=input_features.columns, data=model.x_weights_)


def calculate_y_weights(model, target_features):
    return pd.DataFrame(index=target_features.columns, data=model.y_weights_)
