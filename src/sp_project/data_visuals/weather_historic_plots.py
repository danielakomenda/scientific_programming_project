import pandas as pd
import matplotlib.pyplot as plt
import bokeh.models
import bokeh.plotting
import bokeh.io
import bokeh.layouts
import bokeh.palettes
import bokeh.transform
import bokeh.embed


def weather_overview_plot(data):

    day_source = bokeh.models.ColumnDataSource(data=data)

    middle = data.index[len(data) // 2]
    selection_range = pd.Timedelta("20 days")


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

    p.yaxis.axis_label = 'Weather'

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
        fig.extra_y_ranges['rain'] = bokeh.models.Range1d(0, data.rain.max()+1, bounds=(0, None))

        fig.vbar(
            x='date',
            top="rain",
            source=day_source,
            color="#0072B2",
            legend_label="Rain",
            width=pd.Timedelta(hours=20),
            y_range_name="rain",
        )

        fig.line(
            x='date',
            y="avg_temp",
            source=day_source,
            color="#D55E00",
            legend_label="Temperature",
        )

    ax2 = bokeh.models.LinearAxis(y_range_name="rain", axis_label="rain [mm/h]")
    ax2.axis_label_text_color = "navy"
    p.add_layout(ax2, 'right')

    p.legend.location = "top_left"

    range_tool = bokeh.models.RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    overview.ygrid.grid_line_color = None
    overview.add_tools(range_tool)

    fig = bokeh.layouts.column(p, overview)

    return fig


async def wetter2_boxplot(data):
    temp = data.avg_temp
    plot = plt.boxplot(temp)
    return plot


async def wetter2_histplot(data):
    temp = data.avg_temp
    plot = plt.hist(temp, edgecolor='black', linewidth=1.2)
    return plot
