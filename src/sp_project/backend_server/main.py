import logging
import sys

import quart
from bokeh.resources import CDN
from markupsafe import Markup
import anyio
import folium



logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = quart.Quart(__name__)


def run() -> None:
    app.run()


@app.get("/")
async def main_page():
    return await quart.render_template("model.html", resources=Markup(CDN.render()))


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


@app.get('/prediction')
async def predict(lon:float, lat:float):
    pass


@app.get('/map')
async def map():
    # create a Folium map
    m = folium.Map(location=[51.5074, -0.1278], zoom_start=12)

    # add a marker to the map
    folium.Marker(location=[51.5074, -0.1278], popup='London').add_to(m)

    # render the HTML template with the map
    return await quart.render_template('model.html', map=m._repr_html_())



if __name__ == "__main__":
    app.run()