import itertools
from textwrap import dedent
from typing import Iterable

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from cumulative_snow import load_data
from cumulative_snow.args import Args


def plot_cumulative_annual(args: Args) -> None:
    if not args.output_path:
        return

    data = load_data.load_noaa_data(args)

    bool_mask = pd.Series(True, data.index)
    if args.start_year:
        bool_mask &= data["WINTER_YEAR"] >= args.start_year.year
    if args.end_year:
        bool_mask &= data["WINTER_YEAR"] <= args.end_year.year
    data = data[bool_mask]

    figs = itertools.chain(
        _plot_continuous(data),
        _plot_overlapping(data),
        _plot_monthly_averages(data),
    )

    first_idx = data.first_valid_index()
    location_name = data["NAME"][first_idx]
    location_id = data["STATION"][first_idx]
    page_title = f"Cumulative Snow per Winter Season at {location_name} ({location_id})"

    with open(args.output_path, "w") as f:
        f.write(
            dedent(f"""\
            <html>
                <head>
                    <title>{page_title}</title>
                    <style>
                    #root {{
                        display: flex;
                        margin: auto;
                        flex-wrap: wrap;
                        justify-content: center;
                    }}

                    </style>
                </head>
                <body>
                    <h1>{page_title}</h1>
                    <div id="root">
            """)
        )
        for i, fig in enumerate(figs):
            # Include the JS engine only once to keep the file small
            include_js = "cdn" if i == 0 else False
            fig.write_html(
                f,
                default_height=800,
                default_width=1000,
                full_html=False,
                include_plotlyjs=include_js,
            )
            if args.save_svgs:
                fig.write_image(
                    f"{args.output_path}.{i}.svg", format="svg", height=600, width=1000
                )

        f.write(
            dedent("""\
                    </div>
                </body>
            </html>
            """)
        )


def _plot_continuous(data: pd.DataFrame) -> Iterable[go.Figure]:
    yield px.line(
        data,
        x="DATE",
        y="CUMULATIVE_SNOW",
        color="WINTER_YEAR",
        title="Cumulative Snow per Winter Season",
        labels={"CUMULATIVE_SNOW": "Snowfall (inches)", "DATE": "Date"},
    )


def _plot_overlapping(data: pd.DataFrame) -> Iterable[go.Figure]:
    data = data.copy()

    # Normalize to the 1999-2000 winter year. Note 2000 includes the leap day.
    data["NORMALIZED_WINTER_DATE"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": (
                    data["DATE"].dt.year - data["WINTER_SEASON_START"].dt.year + 1999
                ),
                "month": data["DATE"].dt.month,
                "day": data["DATE"].dt.day,
            }
        )
    )

    yield px.line(
        data,
        x="NORMALIZED_WINTER_DATE",
        y="CUMULATIVE_SNOW",
        color="WINTER_YEAR",
        title="Cumulative Snow per Winter Season (Overlapping Years)",
        labels={
            "CUMULATIVE_SNOW": "Snowfall (inches)",
            "NORMALIZED_WINTER_DATE": "Date in Winter Season",
        },
    ).update_xaxes(tickformat="%b %d")

    data_days_with_snow = data[data["SNOW"] > 0]
    yield px.scatter(
        data_days_with_snow,
        x="NORMALIZED_WINTER_DATE",
        y="SNOW",
        marginal_x="histogram",
        marginal_y="histogram",
        title="Scatter all Snow Days in all Years",
        labels={
            "SNOW": "Snowfall (inches)",
            "NORMALIZED_WINTER_DATE": "Date in Winter Season",
        },
    ).update_xaxes(tickformat="%b %d")

    yield px.density_heatmap(
        data_days_with_snow,
        x="NORMALIZED_WINTER_DATE",
        y="SNOW",
        text_auto=True,
        nbinsx=30,
        nbinsy=30,
        color_continuous_scale="Blues",
        title="Heatmap of Snow",
        labels={
            "SNOW": "Snowfall (inches)",
            "NORMALIZED_WINTER_DATE": "Date in Winter Season",
        },
    ).update_xaxes(tickformat="%b %d")

    yield px.violin(
        data_days_with_snow,
        x="WINTER_YEAR",
        y="SNOW",
        points="all",
        color="WINTER_YEAR",
        title="Violin Plot of Snow",
        labels={
            "SNOW": "Snowfall (inches)",
            "WINTER_YEAR": "Winter Year",
        },
    )


def _plot_monthly_averages(data: pd.DataFrame) -> Iterable[go.Figure]:
    month_order = [
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
    ]

    # 1. Sum daily data into specific month-year buckets
    # (e.g., Total snow in Jan 2020, Total snow in Jan 2021...)
    monthly_summaries = (
        data.groupby(
            [
                data["DATE"].dt.year.rename("YEAR"),
                data["DATE"].dt.strftime("%b").rename("MONTH"),
            ]
        )
        .agg({"TAVG": "mean", "TMAX": "mean", "TMIN": "mean", "SNOW": "sum"})
        # move grouped index into regular columns
        .reset_index()
    )

    final_data = monthly_summaries.groupby("MONTH").mean(numeric_only=True)
    final_data = final_data.reindex(month_order)

    fig = px.bar(
        final_data,
        x=final_data.index,
        y=["SNOW", "TAVG", "TMAX", "TMIN"],
        title="Monthly Averages",
        barmode="group",
        template="ggplot2",
        labels={
            "SNOW": "Snowfall (inches)",
            "TAVG": "Avg Temp",
            "TMAX": "Max Temp",
            "TMIN": "Min Temp",
        },
    )

    # Hacks to get dual axis with separate units
    fig.update_layout(
        yaxis2=dict(title="Degrees (°F)", side="right", overlaying="y", showgrid=False),
        yaxis_title="Snowfall (Inches)",
    )
    fig.update_traces(yaxis="y2", selector=lambda t: t.name in ["TAVG", "TMAX", "TMIN"])
    fig.update_traces(yaxis="y1", selector=lambda t: t.name == "SNOW")

    yield fig
