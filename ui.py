"""UI."""

from dash import Dash, dcc, html

from db import DB

import pandas as pd

from plotly_calplot import calplot


class UI:
    """UI class."""

    def __init__(self, *, db: DB):
        """
        Construct UI class.

        Parameters:
            db (DB): database instance
        """
        self._db = db

    def _layout(self):
        con = self._db.get_con()
        df = pd.read_sql_query("SELECT count(id) AS reboots, "
                               "strftime('%Y-%m-%d', timestamp) AS date "
                               "FROM events "
                               "WHERE type = 'router_reboot' "
                               "GROUP BY strftime('%Y-%m-%d', timestamp)",
                               con,
                               parse_dates=['date'])

        fig_cal = calplot(df, x='date', y='reboots',
                          month_lines=False,
                          colorscale='burg',
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
