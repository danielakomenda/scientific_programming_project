import json
import logging
import sys
import pickle

import quart.flask_patch
import flask_caching

import quart
import bokeh.resources
import markupsafe
import bokeh.embed

from sp_project.data_collection.openweather_api_client import OpenWeatherClient
from sp_project.data_visuals.weather_historic_plots import weather_overview_plot
from sp_project.data_preparation.db_entsoe import *
from sp_project.data_preparation.db_openweather_historic import *
from sp_project.data_visuals.energy_historic_plots import *
from sp_project.data_visuals.energy_prediction_plots import *
from sp_project.data_visuals.weather_prediction_plots import *


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = quart.Quart(__name__)
cache = flask_caching.Cache(config={'CACHE_TYPE': 'SimpleCache'})

cache.init_app(app)


app_state = AppState()


@app.while_serving
async def app_lifecycle():
    app_state.db_client = get_global_db_client()
    with open(app.root_path/"assets/prediction-model.pickle", "rb") as fh:
        app_state.model = pickle.load(fh)
    async with OpenWeatherClient(
        api_key="***REMOVED***",
    ) as ow_client:
        app_state.ow_client = ow_client
        yield


def run() -> None:
    app.run()


@app.get('/')
async def main_page():
    return await quart.render_template("main.html", resources=markupsafe.Markup(bokeh.resources.CDN.render()))


@app.get('/pages/<string:p>')
async def web_pages(p):
    return await quart.render_template(f"{p}.html", resources=markupsafe.Markup(bokeh.resources.CDN.render()))


@app.get('/Historic-Energy-Production')
@cache.cached()
async def energy_historic():
    try:
        raw_result = await extract_energy_data_raw()
        daily_result = await extract_energy_data_daily()

        # energy_historic_grouped_barplot = energy_grouped_bar_plot(daily_result)
        energy_historic_plot = energy_overview_plot(raw_result=raw_result, daily_result=daily_result)
        energy_historic_pie = energy_yearly_pieplot(daily_result)

        data = json.dumps(dict(
            # plot1=bokeh.embed.json_item(energy_historic_grouped_barplot),
            plot2=bokeh.embed.json_item(energy_historic_plot),
            plot3=bokeh.embed.json_item(energy_historic_pie),
        ))
        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        return flask_caching.CachedResponse(
            response=response,
            timeout=86400,
        )
    except Exception as ex:
        import traceback
        return dict(
            error=repr(ex),
            traceback=traceback.format_exc(),
        )


@app.get('/Historic-Weather-Data')
@cache.cached()
async def weather_historic():
    try:
        result = await extract_data_daily()
        weather_historic_plot = weather_overview_plot(result)
        data = json.dumps(dict(
            plot1=bokeh.embed.json_item(weather_historic_plot),
        ))
        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        return flask_caching.CachedResponse(
            response=response,
            timeout=86400,
        )
    except Exception as ex:
        import traceback
        return dict(
            error=repr(ex),
            traceback=traceback.format_exc(),
        )


@app.get('/Energy-Prediction')
async def energy_predict():
    try:
        lat = float(quart.request.args["lat"])
        lon = float(quart.request.args["lon"])

        result = await extract_predictions_daily(app_state, lon=lon, lat=lat)
        features = prepare_prediction_features(result, lat)
        prediction = energy_prediction(app_state.model, features)

        energy_prediction_plot = energy_prediction_interactive_plot(prediction)
        energy_prediction_pie = energy_prediction_pieplot(prediction)

        data = json.dumps(dict(
            energy_prediction_plot1=bokeh.embed.json_item(energy_prediction_plot),
            energy_prediction_plot2=bokeh.embed.json_item(energy_prediction_pie),
        ))
        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        return response
    except Exception as ex:
        import traceback
        return dict(
            error=repr(ex),
            traceback=traceback.format_exc(),
        )


@app.get('/Weather-Prediction')
async def weather_predict():
    try:
        lat = float(quart.request.args["lat"])
        lon = float(quart.request.args["lon"])
        result = await extract_predictions_daily(app_state, lon=lon, lat=lat)
        weather_prediction_plot = weather_prediction_interactive_plot(result)
        data = json.dumps(dict(
            weather_prediction_plot=bokeh.embed.json_item(weather_prediction_plot),
        ))
        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        return response
    except Exception as ex:
        import traceback
        return dict(
            error=repr(ex),
            traceback=traceback.format_exc(),
        )


if __name__ == "__main__":
    app.run(port=5001)
