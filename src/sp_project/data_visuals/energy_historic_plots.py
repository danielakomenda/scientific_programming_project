import datetime

import matplotlib.pyplot as plt
import pandas as pd
import math
import bokeh.transform
import bokeh.models
import bokeh.plotting
import bokeh.layouts
import bokeh.embed
import bokeh.io


def energy_grouped_bar_plot(result):
    fig, ax = plt.subplots()

    color = "#BBBBBB #F0E442 #D55E00 #009E73 #0072B2 #56B4E9".split()

    avg_daily_production = result.iloc[:, :-1].groupby(result.index.year).mean()
    avg_daily_production.plot.bar(ax=ax, color=color)

    ax.set_ylabel('Average Energy Production [MW]')
    ax.set_title('Average Energy Production by Year and Source')
    ax.legend()

    return fig


def energy_overview_plot(raw_result, daily_result):
    raw_source = bokeh.models.ColumnDataSource(data=raw_result)
    day_source = bokeh.models.ColumnDataSource(data=daily_result)

    column_names = "nuclear solar wind water_reservoir water_river water_pump".split()
    colors = "#D55E00 #F0E442 #BBBBBB #009E73 #0072B2 #56B4E9".split()

    middle = len(raw_result) // 2
    selection_range = 500

    # Selected-Part-Plot
    p = bokeh.plotting.figure(
        height=300,
        width=800,
        x_axis_type="datetime",
        x_axis_location="above",
        x_range=(raw_result.index[middle - selection_range], raw_result.index[middle + selection_range]),
    )

    p.yaxis.axis_label = 'Energy Production [MW]'

    raw_plot = p.varea_stack(
        x='datetime',
        stackers=column_names,
        source=raw_source,
        color=colors,
        legend_label=column_names,
        visible=False,
    )

    daily_plot = p.varea_stack(
        x='date',
        stackers=column_names,
        source=day_source,
        color=colors,
        legend_label=column_names,
    )

    labels = ["Stündlich", "Täglich"]

    plot_selector = bokeh.models.RadioButtonGroup(labels=labels, active=1)
    plot_selector.js_on_event(
        "button_click",
        bokeh.models.CustomJS(
            args=dict(
                btn=plot_selector,
                rplot=raw_plot,
                dplot=daily_plot,
            ),
            code="""
        console.log('radio_button_group: active=' + btn.active, this.toString())    
        let plots=[rplot, dplot]
        plots.forEach(p => p.forEach(q => {q.visible=false}))
        plots[btn.active].forEach(q => {q.visible=true})
    """)
    )

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

    overview.varea_stack(
        x='date',
        stackers=column_names,
        source=day_source,
        color=colors,
    )

    p.legend.location = "top_left"

    range_tool = bokeh.models.RangeTool(x_range=p.x_range)
    range_tool.overlay.fill_color = "navy"
    range_tool.overlay.fill_alpha = 0.2

    overview.ygrid.grid_line_color = None
    overview.add_tools(range_tool)

    fig = bokeh.layouts.column(plot_selector, p, overview)

    return fig


def energy_yearly_pieplot(result):
    years = set(result.index.year)
    for year in years:
        df_energy_year = result[result.index.year == year]

        x = round(df_energy_year.iloc[:, :-1].sum() / 1000, 2)

        data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
        data['angle'] = data['value'] / data['value'].sum() * 2 * math.pi
        data['color'] = "#BBBBBB #F0E442 #D55E00 #009E73 #0072B2 #56B4E9".split()

        p = bokeh.plotting.figure(
            height=350,
            title=f"Yearly Production by Energy-Type in GWh in {year}",
            toolbar_location=None,
            tools="hover",
            tooltips="@country: @value",
            x_range=(-0.5, 1.0),
        )

        p.wedge(
            x=0,
            y=1,
            radius=0.4,
            start_angle=bokeh.transform.cumsum('angle', include_zero=True),
            end_angle=bokeh.transform.cumsum('angle'),
            line_color="white",
            fill_color='color',
            legend_field='country',
            source=data,
        )

        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None

        pie_fig = bokeh.layouts.column(p)

        return pie_fig


def energy_variable_pieplot(result, start_date, end_date):
    start = datetime.datetime(
        year=start_date.year,
        month=start_date.month,
        day=start_date.day
    ).replace(tzinfo=datetime.timezone.utc)

    end = datetime.datetime(
        year=end_date.year,
        month=end_date.month,
        day=end_date.day
    ).replace(tzinfo=datetime.timezone.utc)

    df_energy = result.loc[start:end, :]

    title = f"Production by Energy-Type in MWh from {start.date()} to {end.date()}"

    x = round(df_energy.iloc[:, :-1].sum(), 2)

    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * math.pi
    data['color'] = "#BBBBBB #F0E442 #D55E00 #009E73 #0072B2 #56B4E9".split()

    p = bokeh.plotting.figure(
        height=350,
        title=title,
        toolbar_location=None,
        tools="hover",
        tooltips="@country: @value",
        x_range=(-0.5, 1.0),
    )

    p.wedge(
        x=0,
        y=1,
        radius=0.4,
        start_angle=bokeh.transform.cumsum('angle', include_zero=True),
        end_angle=bokeh.transform.cumsum('angle'),
        line_color="white",
        fill_color='color',
        legend_field='country',
        source=data,
    )

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    pie_fig = bokeh.layouts.column(p)

    return pie_fig
