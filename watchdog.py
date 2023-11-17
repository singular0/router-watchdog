#!/usr/bin/env python3

"""Watchdog process."""

import logging
import os
import sys
from threading import Thread
from time import sleep

from db import DB

from dotenv import load_dotenv

import requests
from requests import RequestException

import schedule

import speedtest

from util import format_speed

from zte_api import ZTEAPI


class Watchdog:
    """Watchdog process class."""

    def __init__(self, *, check_host: str, check_interval: int, retry_interval: int,
                 check_retries: int, check_timeout: int, dry_run: bool = False,
                 router_host: str, router_user: str = None, router_password: str,
                 router_model: str, speedtest_interval: int, db: DB):
        """
        Construct watchdog process class.

        Parameters:
            check_host (str): host to check
            check_interval (int): number of seconds between checks
            retry_interval (int): number of seconds between check retries
            check_retries (int): number of retry attempts before check is considered to be failed
            check_timeout (int): check request timeout in seconds
            speedtest_interval (int): speed test interval in seconds
            dry_run (bool): do not actually reboot the router
            router_host (str): router host
            router_user (str): router user
            router_model (str): router model
            router_password (str): router password
            db (DB): datbase
        """
        self._check_host = check_host
        self._check_interval = check_interval
        self._retry_interval = retry_interval
        self._check_retries = check_retries
        self._check_timeout = check_timeout
        self._dry_run = dry_run
        self._router_host = router_host
        self._router_user = router_user
        self._router_model = router_model
        self._router_password = router_password
        self._speedtest_interval = speedtest_interval
        self._db = db

    def _wait_for_host(self, host, attempts=1, delay=10, timeout=10):
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

    def _check(self):
        logging.debug("Checking WAN [%s]", self._check_host)
        wan_available = self._wait_for_host(self._check_host, delay=self._retry_interval,
                                            attempts=self._check_retries,
                                            timeout=self._check_timeout)
        if not wan_available:
            self._db.save_event("wan_fail")
            logging.debug("Checking router [%s]", self._router_host)
            router_available = self._wait_for_host(self._router_host)
            if router_available:
                self._db.save_event("router_reboot")
                logging.warning("Trying router reboot")
                if self._dry_run:
                    logging.warning("Dry run, reboot skipped")
                else:
                    try:
                        router = ZTEAPI(self._router_host, user=self._router_user,
                                        password=self._router_password, model=self._router_model)
                        router.login()
                        router.reboot()
                    except RequestException:
                        self._db.save_event("router_fail")
                        logging.error("Router unavailable while rebooting")
            else:
                self._db.save_event("router_fail")
                logging.warning("Router unavailable")
        else:
            logging.debug("WAN available")

    def _speedtest(self):
        try:
            logging.debug("Running download speed test")
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download()
            logging.debug(f"Download speed is {format_speed(download)}")
            self._db.save_event("download_test", value=download)
        except Exception as ex:
            logging.error(f"Speed test failed: {ex}")
            self._db.save_event("speedtest_fail")

    def _run(self):
        logging.debug("Running scheduler loop in a thread...")
        while True:
            schedule.run_pending()
            sleep(1)

    def start(self):
        """Start watchdog process."""
        logging.debug(f"Scheduling check every {self._check_interval}s")
        schedule.every(self._check_interval).seconds.do(self._check)

        logging.debug(f"Scheduling speed test every {self._speedtest_interval}s")
        schedule.every(self._speedtest_interval).seconds.do(self._speedtest)

        thread = Thread(target=self._run)
        thread.start()


if __name__ == "__main__":

    load_dotenv()

    router_host = os.environ["ROUTER_HOST"]
    router_user = os.getenv("ROUTER_USER")
    router_password = os.environ["ROUTER_PASSWORD"]
    router_model = os.getenv("ROUTER_MODEL", "MC888")

    check_host = os.getenv("CHECK_HOST", "google.com")
    check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
    check_retry = int(os.getenv("CHECK_RETRY", "3"))
    check_retry_interval = int(os.getenv("CHECK_RETRY_INTERVAL", "10"))
    check_timeout = int(os.getenv("CHECK_TIMEOUT", "10"))

    speedtest_interval = int(os.getenv("SPEEDTEST_INTERVAL", "3600"))

    db_path = os.getenv("DB_PATH", "router-watchdog.db")

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    dry_run = os.getenv("DRY_RUN")

    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[log_handler]
    )

    logging.info("Will check [%s] every %d s", check_host, check_interval)
    logging.info("Will retry %d times with %d s interval", check_retry, check_retry_interval)
    logging.info("HTTP timeout is %d s", check_timeout)
    logging.info("Will check speed every %d s", speedtest_interval)
    logging.info("Router:")
    logging.info("  model: [%s]", router_model)
    logging.info("  address: [%s]", router_host)
    logging.info("  user: [%s], password: [%s]", router_user, "*" * len(router_password))
    logging.info("Logging with level %s", log_level)
    logging.info("Event DB is [%s]", db_path)

    if dry_run:
        logging.info("Dry run mode")

    db = DB(db_path=db_path)

    watchdog = Watchdog(check_host=check_host, check_retries=check_retry,
                        check_timeout=check_timeout, check_interval=check_interval,
                        retry_interval=check_retry_interval, dry_run=dry_run,
                        router_host=router_host, router_password=router_password,
                        router_user=router_user, router_model=router_model,
                        db=db, speedtest_interval=speedtest_interval)
    watchdog.start()
