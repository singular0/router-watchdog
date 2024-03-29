#!/usr/bin/env python3

"""Router watchdog HTTP server."""

import logging
import os
import sys
from datetime import datetime

from dash import Dash, dcc, html

from dotenv import load_dotenv

from flask import Flask

from flask_restful import Api, Resource

import pandas as pd

from plotly_calplot import calplot

import watchdog.util.human_readable as hr
from watchdog.db import DB

db = None


class Stats(Resource):
    """Statistics RESTful API class."""

    def get(self):
        """
        Get statistics data.

        Returns:
            dict: statistics
        """
        stats = {}

        con = db.get_con()
        cur = con.cursor()

        # Uptime
        cur.execute("SELECT max(timestamp) FROM events WHERE type = 'router_reboot'")
        result = cur.fetchone()
        if result:
            last_reboot = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            uptime = datetime.now() - last_reboot
            stats['uptime'] = hr.speed(uptime)

        # Reboots today
        cur.execute("""
            SELECT count(id)
            FROM events
            WHERE
                type = 'router_reboot' AND
                timestamp >= date('now', 'localtime', 'start of day')
        """)
        result = cur.fetchone()
        stats['reboots_today'] = result[0]

        # Average download speed today
        cur.execute("""
            SELECT avg(value)
            FROM events
            WHERE
                type = 'download_test' AND
                timestamp >= date('now', 'localtime', 'start of day')
        """)
        result = cur.fetchone()
        if result:
            stats['avg_dl_speed_today'] = result[0]

        return stats


def _layout():
    graphs = []

    con = db.get_con()
    cur = con.cursor()

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
    if not reboots_df.empty:
        reboots_fig = calplot(reboots_df, x='date', y='reboots',
                              month_lines=False,
                              colorscale='burg',
                              showscale=True,
                              cmap_min=0,
                              title='Router Reboots')
        graphs.append(dcc.Graph(id='reboots_graph', figure=reboots_fig))

    # Last download speed
    cur.execute("""
        SELECT value
        FROM events
        WHERE type = 'download_test'
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cur.fetchone()
    if result:
        graphs.append(html.P(f'Last speed {result[0]}'))

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
    if not dl_df.empty:
        dl_fig = calplot(dl_df, x='date', y='avg_download_speed',
                         month_lines=False,
                         colorscale='rdylgn',
                         showscale=True,
                         cmap_min=0,
                         title='Average Download Speed')
        graphs.append(dcc.Graph(id='dl_graph', figure=dl_fig))

    return html.Div(graphs)


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
