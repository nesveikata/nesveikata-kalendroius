import calendar
import locale
from datetime import date, datetime

import pandas as pd
from arcgis.gis import GIS
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from plotly_calplot.layout_formatter import showscale_of_heatmaps
from plotly_calplot.single_year_calplot import year_calplot
from plotly_calplot.utils import fill_empty_with_zeros


def add_curr_day_square(cplt: go.Figure, pad: bool = True) -> go.Figure:
    kwargs = dict(type="rect", line=dict(color="black", width=3))
    weeknum = int(date.today().strftime("%W"))
    weekday = date.today().weekday()

    _pad = 0
    if pad:
        # spėjau 52 savaitės, kiekviena celė turės 2 padus iš abiejų pusių (ir iš viršaus/apačios)
        # kompensuojam už šalimai esančias celes *= 2. 52*2*2=208
        _pad = -cplt.data[0].xgap / 208

    cplt.add_shape(
        x0=weeknum - 0.5 - _pad,
        y0=weekday - 0.5 - _pad,
        x1=weeknum + 0.5 + _pad,
        y1=weekday + 0.5 + _pad,
        **kwargs,
    )
    return cplt


def localized_month_names() -> list[str]:
    return [month.capitalize() for month in calendar.month_name[1:]]


def localized_day_names(trim: "int | None" = None) -> list[str]:
    return [day[:trim] if trim is not None else day for day in calendar.day_name]


def format_plot_name(system: str) -> str:
    if system.lower() != "bendra":
        return f"Sistemos {system} gedimai"
    return "Bendras sistemų gedimas"


def main() -> None:
    """Prepares data and then plots"""
    gis = GIS()
    item = gis.content.get("a1ba47fe67f247b8a050cfc711066150")
    sdf = pd.DataFrame.spatial.from_layer(item.layers[0])
    df = sdf.groupby("data")[["kiekis", "neveikia_sistema"]].apply(sum).reset_index()
    sistemos = set(sdf["neveikia_sistema"])
    sistemos.add("Bendra")
    df["data"] = pd.to_datetime(df["data"].dt.strftime("%Y-%m-%d"))
    sistemos = sorted(sistemos)
    fig = make_subplots(
        rows=len(sistemos),
        cols=1,
        subplot_titles=(list(format_plot_name(system) for system in sistemos)),
    )

    for i, sistema in enumerate(sistemos):
        data_subset = df
        if sistema.lower() != "bendra":
            data_subset = df[df["neveikia_sistema"].str.contains(sistema)]

        data_subset = fill_empty_with_zeros(
            data_subset, "data", False, datetime.now().year
        )
        plt = year_calplot(
            data_subset,
            x="data",
            y="kiekis",
            name="Kiekis",
            # text=["neveikia_sistema"],
            colorscale="reds",
            gap=3,
            month_lines_width=3,
            month_lines_color="grey",
            fig=fig,
            row=i,
            year=format_plot_name(sistema),
        )

    plt = add_curr_day_square(plt, pad=True)

    xaxis_text = dict(ticktext=localized_month_names())
    yaxis_text = dict(ticktext=localized_day_names(4))

    plt.update_layout(
        title="nEsveikata - Sistemų gedimai",
        xaxis=xaxis_text,
        yaxis=yaxis_text,
        **{f"xaxis{i}": xaxis_text for i in range(1, len(sistemos) + 1)},
        **{f"yaxis{i}": yaxis_text for i in range(1, len(sistemos) + 1)},
    )

    showscale_of_heatmaps(fig)

    layout = dict(
        height=270 * len(sistemos),
        width=1350,
        yaxis_scaleanchor="x",
        margin=dict(
            b=50,
            t=50,
        ),
        font={"size": 10, "color": "black"},
        plot_bgcolor="LightSteelBlue",
        paper_bgcolor="LightSteelBlue",
    )
    fig.update_layout(layout)
    fig.write_html("html/index.html")


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "lt_LT")
    main()
