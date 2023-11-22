"""Watchdog."""

import logging
import os
import sys
from enum import Enum
from threading import Thread
from time import sleep

from dotenv import load_dotenv

import requests
from requests import RequestException

import schedule

import speedtest

from ..db import DB
from ..devices.zte_router import ZTERouter
from ..util import human_readable as hr


class WatchdogEvent(Enum):
    """Watchdog events."""

    DownloadTest = 'download_test'
    RouterFail = 'router_fail'
    RouterReboot = 'router_reboot'
    SpeedtestFail = 'speedtest_fail'
    WANFail = 'wan_fail'


class Watchdog:
    """Watchdog process class."""

    def __init__(self, *, event_handler: callable):
        """
        Construct watchdog process class.

        Parameters:
            event_handler (callable): event handler callback
        """
        self._event_handler = event_handler

        self._check_host = os.getenv("CHECK_HOST", "google.com")
        self._check_interval = int(os.getenv("CHECK_INTERVAL", "60"))
        self._check_retry = int(os.getenv("CHECK_RETRY", "3"))
        self._check_timeout = int(os.getenv("CHECK_TIMEOUT", "10"))
        self._check_retry_interval = int(os.getenv("CHECK_RETRY_INTERVAL", "10"))

        self._speedtest_interval = int(os.getenv("SPEEDTEST_INTERVAL", "3600"))

        logging.info(f"Will check [{self._check_host}] every {self._check_interval}s")
        logging.info(f"Will retry {self._check_retry} times "
                     f"with {self._check_retry_interval}s interval")
        logging.info(f"HTTP timeout is {self._check_timeout}s")

        if self._speedtest_interval:
            logging.info(f"Will check speed every {self._speedtest_interval}s")

    def _wait_for_host(self, host, attempts=1, delay=10, timeout=10):
        remaining_attempts = attempts
        while True:
            try:
                requests.head(f"http://{host}", timeout=timeout)
                return True
            except RequestException:
                remaining_attempts -= 1
                if remaining_attempts > 0:
                    logging.warning(f"Connection to {host} failed, "
                                    f"will retry {remaining_attempts} more times")
                    sleep(delay)
                else:
                    logging.warning(f"{host} is unavailable")
                    return False

    def _check(self):
        logging.debug(f"Checking WAN [{self._check_host}]")
        wan_available = self._wait_for_host(self._check_host, delay=self._check_retry_interval,
                                            attempts=self._check_retry,
                                            timeout=self._check_timeout)
        if not wan_available:
            self._event_handler(WatchdogEvent.WANFail)
            logging.debug(f"Checking router [{self._router_host}]")
            router_available = self._wait_for_host(self._router_host)
            if router_available:
                self._event_handler(WatchdogEvent.RouterReboot)
                logging.warning("Trying router reboot")
                if self._dry_run:
                    logging.warning("Dry run, reboot skipped")
                else:
                    try:
                        self._device.reboot()
                    except RequestException:
                        self._event_handler(WatchdogEvent.RouterFail)
                        logging.error("Router unavailable while rebooting")
            else:
                self._event_handler(WatchdogEvent.RouterFail)
                logging.warning("Router unavailable")
        else:
            logging.debug("WAN available")

    def _speedtest(self):
        try:
            logging.debug("Running download speed test")
            st = speedtest.Speedtest()
            st.get_best_server()
            download = st.download()
            logging.debug(f"Download speed is {hr.speed(download)}")
            self._event_handler(WatchdogEvent.DownloadTest, value=download)
        except Exception as ex:
            logging.error(f"Speed test failed: {ex}")
            self._event_handler(WatchdogEvent.SpeedtestFail)

    def _scheduler(self):
        logging.debug("Running scheduler loop in a thread...")
        while True:
            schedule.run_pending()
            sleep(1)

    def start(self):
        """Start watchdog process."""
        logging.debug(f"Scheduling check every {self._check_interval}s")
        schedule.every(self._check_interval).seconds.do(self._check)

        if self._speedtest_interval:
            logging.debug(f"Scheduling speed test every {self._speedtest_interval}s")
            schedule.every(self._speedtest_interval).seconds.do(self._speedtest)

        thread = Thread(target=self._scheduler)
        thread.start()


if __name__ == "__main__":

    load_dotenv()

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[log_handler]
    )
    logging.info(f"Logging with level {log_level}")

    db_path = os.getenv("DB_PATH", "router-watchdog.db")
    logging.info(f"Event DB is [{db_path}]")
    db = DB(db_path=db_path)

    dry_run = os.getenv("DRY_RUN")
    if dry_run:
        logging.warning(f"Dry run mode (DRY_RUN={dry_run})")

    device = ZTERouter()

    def _event_handler(event: WatchdogEvent, value: float = 0):
        db.save_event(event.value, value)
        if event == WatchdogEvent.RouterReboot:
            if dry_run:
                logging.warning("Dry run, reboot skipped")
            else:
                try:
                    device.reboot()
                except RequestException:
                    db.save_event(event.value, value)
                    logging.error("Router unavailable while rebooting")

    watchdog = Watchdog(event_handler=_event_handler)
    watchdog.start()
