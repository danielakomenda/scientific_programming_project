import logging
import sys

import quart

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

app = quart.Quart(__name__)


def run() -> None:
    app.run()

@app.get("/")
async def main_page():
    return await quart.render_template("main.html")

