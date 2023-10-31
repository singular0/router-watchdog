#!/usr/bin/env python3

"""Router watchdog."""

import logging
import os
import sqlite3
import sys
from time import sleep

from dotenv import load_dotenv

import requests
from requests import RequestException

import schedule


from zte_api import ZTEAPI


def _wait_for_host(host, attempts=1, delay=10, timeout=10):
    remaining_attempts = attempts
    while True:
        try:
            requests.head(f"http://{host}", timeout=timeout)
            return True
        except RequestException:
            remaining_attempts -= 1
            if remaining_attempts > 0:
                logging.warning("Connection to %s failed, will retry %d more times",
                                host, remaining_attempts)
                sleep(delay)
            else:
                logging.warning("%s is unavailable", host)
                return False


def _save_event(event_type):
    cur.execute("INSERT INTO events (type) VALUES (?)", [event_type])
    con.commit()


def _check():
    logging.debug("Checking WAN [%s]", check_host)
    wan_available = _wait_for_host(check_host, delay=check_retry_interval,
                                   attempts=check_retry, timeout=check_timeout)
    if not wan_available:
        _save_event("wan_fail")
        logging.debug("Checking router [%s]", router_host)
        router_available = _wait_for_host(router_host)
        if router_available:
            _save_event("router_reboot")
            logging.warning("Trying router reboot")
            if dry_run:
                logging.warning("Dry run, reboot skipped")
            else:
                try:
                    router = ZTEAPI(router_host, password=router_password)
                    router.login()
                    router.reboot()
                except RequestException:
                    _save_event("router_fail")
                    logging.error("Router unavailable while rebooting")
        else:
            _save_event("router_fail")
            logging.warning("Router unavailable")
    else:
        logging.debug("WAN available")


if __name__ == "__main__":

    load_dotenv()

    router_host = os.environ["ROUTER_HOST"]
    router_password = os.environ["ROUTER_PASSWORD"]

    check_host = os.getenv("CHECK_HOST", "google.com")
    check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
    check_retry = int(os.getenv("CHECK_RETRY", "3"))
    check_retry_interval = int(os.getenv("CHECK_RETRY_INTERVAL", "10"))
    check_timeout = int(os.getenv("CHECK_TIMEOUT", "10"))

    db_path = os.getenv("DB_PATH", "router-watchdog.db")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    dry_run = os.getenv("DRY_RUN")

    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[log_handler]
    )

    logging.info("Will check [%s] every %d min", check_host, check_interval)
    logging.info("Will retry %d times with %d s interval", check_retry, check_retry_interval)
    logging.info("HTTP timeout is %d s", check_timeout)
    logging.info("Router is [%s], password is [%s]", router_host, "*" * len(router_password))
    logging.info("Logging with level %s", log_level)
    logging.info("Event DB is [%s]", db_path)

    if dry_run:
        logging.info("Dry run mode")

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS events (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                "timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL, " +
                "type VARCHAR(16) NOT NULL)")

    schedule.every(check_interval).seconds.do(_check)

    while True:
        schedule.run_pending()
        sleep(1)
