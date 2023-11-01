#!/usr/bin/env python3

"""Router watchdog HTTP server."""

import logging
import os
import sys
from datetime import datetime
from time import time

from dash import Dash, dcc, html

from db import DB

from dotenv import load_dotenv

from flask import Flask

from flask_restful import Api, Resource

import pandas as pd

from plotly_calplot import calplot


db = None


def _diff_times(time1: int, time2: int):
    dsec = time1 - time2
    dmin = int(dsec / 60)
    dsec = int(dsec % 60)
    if dmin < 60:
        return f'{dmin:02}:{dsec:02}'
    dhour = int(dmin / 60)
    dmin = int(dmin % 60)
    if dhour < 24:
        return f'{dhour:02}:{dmin:02}:{dsec:02}'
    dday = int(dhour / 24)
    dhour = int(dhour % 24)
    return f'{dday:} days {dhour:02}:{dmin:02}:{dsec:02}'


class Stats(Resource):
    """Statistics RESTful API class."""

    def get(self):
        """
        Get statistics data.

        Returns:
            dict: statistics
        """
        con = db.get_con()
        cur = con.cursor()
        cur.execute("SELECT max(timestamp) FROM events")
        result = cur.fetchone()
        last_reboot_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S').timestamp()
        uptime = _diff_times(time(), last_reboot_time)
        return {'uptime': uptime}


def _layout():
    con = db.get_con()
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


if __name__ == "__main__":

    load_dotenv()

    db_path = os.getenv("DB_PATH", "router-watchdog.db")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[log_handler]
    )

    logging.info("Logging with level %s", log_level)
    logging.info("Event DB is [%s]", db_path)

    db = DB(db_path=db_path)

    logging.debug("Starting web server...")
    server = Flask('router-watchdog')
    app = Dash(server=server)
    api = Api(server)
    api.add_resource(Stats, '/stats')
    app.layout = _layout
    app.run(debug=True, host='0.0.0.0')
