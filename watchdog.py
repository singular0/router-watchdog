"""Watchdog process."""

import logging
from threading import Thread
from time import sleep

from db import DB

import requests
from requests import RequestException

import schedule

from zte_api import ZTEAPI


class Watchdog:
    """Watchdog process class."""

    def __init__(self, *, check_host: str, check_interval: int, retry_interval: int,
                 check_retries: int, check_timeout: int, dry_run: bool = False,
                 router_host: str, router_password: str, db: DB):
        """
        Construct watchdog process class.

        Parameters:
            check_host (str): host to check
            check_interval (int): number of seconds between checks
            retry_interval (int): number of seconds between check retries
            check_retries (int): number of retry attempts before check is considered to be failed
            check_timeout (int): check request timeout in seconds
            dry_run (bool): do not actually reboot the router
            router_host (str): router host
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
        self._router_pasword = router_password
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
        logging.debug("Checking WAN [%s]", self._host)
        wan_available = self._wait_for_host(self._host, delay=self._retry_interval,
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
                        router = ZTEAPI(self._router_host, password=self._router_password)
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

    def _run(self):
        while True:
            schedule.run_pending()
            sleep(1)

    def start(self):
        """Start watchdog process."""
        schedule.every(self._check_interval).seconds.do(self._check)

        Thread(target=self._run)
