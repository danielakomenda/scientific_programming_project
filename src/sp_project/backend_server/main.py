import json
import logging
import sys
import pickle

import quart
from bokeh.resources import CDN
from markupsafe import Markup
import anyio
import bokeh.embed

# from sp_project.app_state import AppState
from sp_project.data_collection.openweather_api_client import OpenWeatherClient
from sp_project.data_preparation.db_client import get_global_db_client
from sp_project.data_preparation.prediction_preparation import *
# from data.prediction import fetch_prediction_daily
from sp_project.data_modelling.model_visuals import prediction_bokeh_plot

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = quart.Quart(__name__)

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
    return await quart.render_template("model.html", resources=Markup(CDN.render()))

@app.get('/pages/<string:p>')
async def web_pages(p):
    return await quart.render_template(f"{p}.html", resources=Markup(CDN.render()))



@app.get('/plot')
async def plot():
    async with await anyio.open_file(app.static_folder/"test.json", "rt", encoding="UTF-8") as fh:
        data = await fh.read()

    # answer from stackoverflow to add the content-type-headers from a document
    response = app.response_class(
        response=data,
        status=200,
        mimetype="application/json",
    )
    return response


@app.get('/prediction-plot')
async def predict():
    try:
        lat = float(quart.request.args["lat"])
        lon = float(quart.request.args["lon"])
        result = await extract_predictions_daily(app_state, lon=lon, lat=lat)
        features = prepare_prediction_features(result, lat)
        prediction = energy_prediction(app_state.model, features)
        prediction_plot = prediction_bokeh_plot(prediction)
        data = json.dumps(dict(plot=bokeh.embed.json_item(prediction_plot)))
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
