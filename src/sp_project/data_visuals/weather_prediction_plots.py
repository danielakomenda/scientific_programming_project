import bokeh.models
import bokeh.plotting
import bokeh.io
import bokeh.layouts
import bokeh.palettes
import bokeh.transform
import bokeh.embed

from sp_project.data_modelling.prediction_preparation import *
from sp_project.notebook_tools import default_clients
import sp_project.app_state


def weather_prediction_interactive_plot(result):
    day_source = bokeh.models.ColumnDataSource(data=result)

    middle = result.index[len(result) // 2]
    selection_range = pd.Timedelta("2 days")

    # Selected-Part-Plot
    p = bokeh.plotting.figure(
        height=300,
        width=800,
        x_axis_type="datetime",
        x_axis_location="above",
        x_range=(middle - selection_range, middle + selection_range),
    )

    for tool in [bokeh.models.PanTool, bokeh.models.WheelZoomTool]:
        p.select_one(tool).dimensions = "width"

    # Overview-Plot
    overview = bokeh.plotting.figure(
        title="Drag the middle and edges of the selection box to change the range above",
        height=130,
        width=800,
        y_range=p.y_range,
        x_axis_type="datetime",
        y_axis_type=None,
        tools="hover",
        toolbar_location=None,
    )

    for fig in [p, overview]:
        fig.extra_y_ranges['rain'] = bokeh.models.Range1d(0, result.rain.max(), bounds=(0, None))

        fig.vbar(
            x='dt',
            top="rain",
            source=day_source,
            color="#0072B2",
            legend_label="Rain",
            width=pd.Timedelta(hours=20),
            y_range_name="rain",
        )

        fig.line(
            x='dt',
            y="temperature",
            source=day_source,
            color="#D55E00",
            legend_label="Temperature",
        )

    p.yaxis.axis_label = 'temperature [°C]'
    p.yaxis.axis_label_text_color = "#D55E00"

    rain_ax = bokeh.models.LinearAxis(y_range_name="rain", axis_label="rain [mm/h]")
    rain_ax.axis_label_text_color = "#0072B2"
    p.add_layout(rain_ax, 'right')

    p.legend.location = "top_left"

    range_tool = bokeh.models.RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    overview.ygrid.grid_line_color = None
    overview.add_tools(range_tool)

    prediction_fig = bokeh.layouts.column(p, overview)

    return prediction_fig