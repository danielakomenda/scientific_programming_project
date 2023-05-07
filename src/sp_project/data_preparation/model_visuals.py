import bokeh.layouts  # import column
import bokeh.models  # import ColumnDataSource, RangeTool
import bokeh.plotting  # import figure, show
import bokeh.palettes


def prediction_bokeh_plot(prediction):
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
