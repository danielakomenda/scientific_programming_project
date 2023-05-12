import pandas as pd
import numpy as np
import bokeh.layouts
import bokeh.models
import bokeh.plotting
import bokeh.palettes
import bokeh.plotting
import bokeh.transform


def energy_prediction_interactive_plot(prediction):
    prediction_source = bokeh.models.ColumnDataSource(prediction)

    column_names = "nuclear solar wind water_reservoir water_pump water_river".split()
    colors = "#D55E00 #F0E442 #BBBBBB #009E73 #0072B2 #56B4E9".split()

    middle = len(prediction) // 2
    selection_range = 2

    # Selected-Part-Plot
    p = bokeh.plotting.figure(
        height=300,
        width=800,
        x_axis_type="datetime",
        x_axis_location="above",
        x_range=(prediction.index[middle - selection_range], prediction.index[middle + selection_range]),
    )

    p.yaxis.axis_label = 'Energy Production [MW]'

    p.varea_stack(
        x='dt',
        stackers=column_names,
        source=prediction_source,
        color=colors,
        legend_label=column_names,
    )

    # Overview-Plot
    overview = bokeh.plotting.figure(
        title="Drag the middle and edges of the selection box to change the range above",
        height=130,
        width=800,
        x_axis_type="datetime",
        y_range=p.y_range,
        y_axis_type=None,
        tools="hover",
        toolbar_location=None,
    )

    overview.varea_stack(
        x='dt',
        stackers=column_names,
        source=prediction_source,
        color=colors,
    )

    p.legend.location = "top_left"

    range_tool = bokeh.models.RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    overview.ygrid.grid_line_color = None
    overview.add_tools(range_tool)

    fig = bokeh.layouts.column(p, overview)

    return fig


def prediction_bokeh_line_plot(prediction):
    source = bokeh.models.ColumnDataSource(data=prediction)

    p = bokeh.plotting.figure(
        height=300,
        width=800,
        x_axis_type="datetime",
        x_axis_location="above",
        x_range=(prediction.index[0], prediction.index[-1]),
    )

    p.yaxis.axis_label = 'Energy Production [MW]'

    for col_name, color in zip(prediction.columns, bokeh.palettes.Colorblind[prediction.shape[1]]):
        p.line('dt', col_name, source=source, line_color=color)

    fig = bokeh.layouts.column(p)
    return fig


def energy_prediction_pieplot(prediction):

    x = round(prediction.iloc[:, :-1].sum(), 2)

    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * np.pi
    data['color'] = "#BBBBBB #F0E442 #D55E00 #009E73 #0072B2 #56B4E9".split()

    p = bokeh.plotting.figure(
        height=350,
        title="Average Production for the next 8 Days",
        toolbar_location=None,
        tools="hover",
        tooltips="@country: @value",
        x_range=(-0.5, 1.0)
    )

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=bokeh.transform.cumsum('angle', include_zero=True), end_angle=bokeh.transform.cumsum('angle'),
            line_color="white", fill_color='color', legend_field='country', source=data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    pie_fig = bokeh.layouts.column(p)

    return pie_fig
