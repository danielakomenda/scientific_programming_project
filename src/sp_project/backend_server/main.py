import logging
import sys

import quart
from bokeh.resources import CDN
from markupsafe import Markup
import anyio



logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = quart.Quart(__name__)


def run() -> None:
    app.run()


@app.get("/")
async def main_page():
    return await quart.render_template("main.html", resources=Markup(CDN.render()))


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


if __name__ == "__main__":
    app.run()