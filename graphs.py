#!/usr/bin/python3
"""makes pretty graphs"""
import datetime
import pickle
import sys

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

# check for pickled data
try:
    with open("database.pkl", mode="rb") as pfile:
        database = pickle.load(pfile)
    print("Found pickled data. Creating graphs.")
except IOError:
    print("No pickled data found.")
    sys.exit(0)


# create stats
all_movies = pd.DataFrame(
    list(database.values()),
    columns=["length", "date"],
)


all_movies["date"] = pd.to_datetime(all_movies["date"])
#  movies['length'] = movies['length'].astype(int)
all_movies.sort_values(by="date", inplace=True, ignore_index=True)
all_movies["average"] = all_movies["length"].expanding().mean()

movies = all_movies.copy(deep=True)

movies = movies[movies["date"].dt.year >= 2015].reset_index(drop=True)
movies["target"] = 120

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=movies["date"],
        y=movies["length"],
        name="Movies",
        mode="markers",
    )
)
fig.add_trace(
    go.Scatter(
        x=movies["date"],
        y=movies["average"],
        name="Cumulative average",
    )
)
# add line to legend
fig.add_trace(
    go.Scatter(
        mode="lines",
        x=movies["date"],
        y=movies["target"],
        name="120m",
        line={"color": "green"},
    ),
)

fig.update_layout(
    template="simple_white",
    legend={
        "orientation": "h",
        "yanchor": "top",
        "y": 1,
        "xanchor": "right",
        "x": 1,
    },
    xaxis_title="Date",
    yaxis_title=r"Movie runtime \ mins",
    xaxis={
        "rangeselector": {
            "buttons": list(
                [
                    {"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
                    {"count": 6, "label": "6m", "step": "month", "stepmode": "backward"},
                    {"count": 1, "label": "1y", "step": "year", "stepmode": "backward"},
                    {"count": 1, "label": "YTD", "step": "year", "stepmode": "todate"},
                    {"step": "all"},
                ]
            )
        },
        "rangeslider": {"visible": True},
        "type": "date",
    },
)

fig.write_html("all.html")
# fig.show()


# yearly
this_year = datetime.datetime.now().year
for year in range(2018, this_year + 1):
    yearly_movies = all_movies[movies["date"].dt.year == year].reset_index(drop=True)
    yearly_movies["average"] = yearly_movies["length"].expanding().mean()
    print(yearly_movies[-20:])

    yearly = go.Figure()
    yearly.add_trace(
        go.Scatter(
            x=yearly_movies["date"],
            y=yearly_movies["length"],
            name="Movies",
            mode="markers",
        )
    )
    yearly.add_trace(
        go.Scatter(
            x=yearly_movies["date"],
            y=yearly_movies["average"],
            name="average",
        )
    )
    yearly.add_hline(y=120, opacity=1, line_width=2, line_color="green")
    yearly.update_layout(
        template="simple_white",
        xaxis_title="Date",
        yaxis_title=r"Movie runtime \ mins",
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": 1,
            "xanchor": "right",
            "x": 1,
        },
    )
    yearly.write_html(f"{year}.html")
    # yearly.show()

    yearly_movies.to_csv(
        f"{year}_avg.txt",
        sep="\t",
        columns=["date", "length", "average"],
        index=False,
    )


# total_by_month = all_movies.groupby(
#    [all_movies['date'].dt.year, all_movies['date'].dt.month]).sum()

total_by_month = all_movies.groupby(all_movies["date"].dt.to_period("M")).sum(numeric_only=True)
total_by_month["date2"] = pd.to_datetime(total_by_month.index.astype(str))
total_by_month.set_index("date2", inplace=True)

# tbm = total_by_month.plot(
tbm, ax = plt.subplots(figsize=(16, 9))
ax.bar(
    x=total_by_month.index,
    height=total_by_month["length"],
    width=20,
)
ax.set_xlabel("Month")
ax.set_ylabel("Time in minutes")
ax.set_title("Cumulative watch time per month")
#  ax.set_xticks(ax.get_xticks()[1:])
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b, %Y"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
plt.xticks(rotation=45, ha="right")
#  tbm = tbm.get_figure()
ax.set_xlim([datetime.date(2018, 12, 15), datetime.datetime.now()])
ax.margins(x=0.05)
tbm.savefig("total_by_month.png", bbox_inches="tight")
