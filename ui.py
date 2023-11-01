"""UI."""

import sqlite3

from dash import Dash, dcc, html

import pandas as pd

from plotly_calplot import calplot


class UI:
    """UI class."""

    def __init__(self, db_path: str):
        """
        Construct UI class.

        Parameters:
            db_path (str): path to SQLite database
        """
        self._db_path = db_path

    def _layout(self):
        con = sqlite3.connect(self._db_path)
        df = pd.read_sql_query("SELECT count(id) AS reboots, "
                               "strftime('%Y-%m-%d', timestamp) AS date "
                               "FROM events "
                               "WHERE type = 'router_reboot' "
                               "GROUP BY strftime('%Y-%m-%d', timestamp)",
                               con,
                               parse_dates=['date'])

        fig_cal = calplot(df, x='date', y='reboots',
                          month_lines=False,
                          colorscale='peach',
                          showscale=True,
                          cmap_min=0,
                          title='Router Reboots')

        return html.Div([
            dcc.Graph(id='graph', figure=fig_cal),
        ])

    def start(self):
        """Start UI webserver."""
        app = Dash(__name__)
        app.layout = self._layout
        app.run(debug=True, host='0.0.0.0')
