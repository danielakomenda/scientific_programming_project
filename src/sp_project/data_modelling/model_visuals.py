import bokeh.layouts  # import column
import bokeh.models  # import ColumnDataSource, RangeTool
import bokeh.plotting  # import figure, show
import bokeh.palettes
import bokeh.plotting
import bokeh.transform
import pandas as pd
import numpy as np


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


def prediction_bokeh_pie_plot(prediction):

    x = round(prediction.iloc[:, :-1].sum(), 2)

    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * np.pi
    data['color'] = bokeh.palettes.Category20c[len(x)]

    p = bokeh.plotting.figure(
        height=350,
        title="Yearly Production by Energy-Type in MWh in 2022",
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
