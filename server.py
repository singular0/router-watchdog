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

from util import diff_times


db = None


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

        # Uptime
        cur.execute("SELECT max(timestamp) FROM events WHERE type = 'router_reboot'")
        result = cur.fetchone()
        uptime = '∞'
        if result:
            last_reboot_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S').timestamp()
            uptime = diff_times(time(), last_reboot_time)

        # Reboots today
        cur.execute("""
            SELECT count(id)
            FROM events
            WHERE
                type = 'router_reboot' AND
                timestamp >= date('now', 'localtime', 'start of day')
        """)
        result = cur.fetchone()
        reboots_today = result[0]

        # Average download speed today
        cur.execute("""
            SELECT avg(value)
            FROM events
            WHERE
                type = 'download_test' AND
                timestamp >= date('now', 'localtime', 'start of day'
        """)
        result = cur.fetchone()
        avg_dl_speed_today = result[0]

        return {
            'uptime': uptime,
            'reboots_today': reboots_today,
            'avg_dl_speed_today': avg_dl_speed_today,
        }


def _layout():
    con = db.get_con()

    # Number of reboots
    query = """
        SELECT
            count(id) AS reboots,
            strftime('%Y-%m-%d', timestamp) AS date
        FROM events
        WHERE type = 'router_reboot'
        GROUP BY strftime('%Y-%m-%d', timestamp)
    """
    reboots_df = pd.read_sql_query(query, con, parse_dates=['date'])
    reboots_fig = calplot(reboots_df, x='date', y='reboots',
                          month_lines=False,
                          colorscale='burg',
                          showscale=True,
                          cmap_min=0,
                          title='Router Reboots')

    # Average download speed
    query = """
        SELECT
            avg(value) AS avg_download_speed,
            strftime('%Y-%m-%d', timestamp) AS date
        FROM events
        WHERE type = 'download_test'
        GROUP BY strftime('%Y-%m-%d', timestamp)
    """
    dl_df = pd.read_sql_query(query, con, parse_dates=['date'])
    dl_fig = calplot(dl_df, x='date', y='avg_download_speed',
                     month_lines=False,
                     colorscale='rdylgn',
                     showscale=True,
                     cmap_min=0,
                     title='Average Download Speed')

    return html.Div([
        dcc.Graph(id='reboots_graph', figure=reboots_fig),
        dcc.Graph(id='dl_graph', figure=dl_fig),
    ])


if __name__ == "__main__":

    load_dotenv()

    db_path = os.getenv("DB_PATH", "router-watchdog.db")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    debug = (log_level == 'DEBUG')

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
    app.run(debug=debug, host='0.0.0.0')
