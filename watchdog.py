#!/usr/bin/env python3

""" Router watchdog """

import logging
import os
import sys

from time import sleep

import requests
import schedule

from dotenv import load_dotenv
from requests import RequestException

from zte_api import ZTEAPI

def wait_for_host(host, attempts=1, delay=10, timeout=10):
    """ Wait for the host to respond to a HTTP request without errors """
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

def check():
    """ Check if the host is available, reboot the router if not """
    logging.debug("Checking WAN [%s]", check_host)
    wan_available = wait_for_host(check_host, delay=check_retry_interval,
                                  attempts=check_attempts, timeout=check_timeout)
    if not wan_available:
        logging.debug("Checking router [%s]", router_host)
        router_available = wait_for_host(router_host)
        if router_available:
            try:
                logging.warning("Trying router reboot")
                if dry_run:
                    logging.warning("Dry run, reboot skipped")
                else:
                    router = ZTEAPI(router_host, router_password)
                    router.login()
                    router.reboot()
            except RequestException:
                logging.error("Router unavailable while rebooting")
        else:
            logging.warning("Router unavailable")
    else:
        logging.debug("WAN available")

if __name__ == "__main__":

    load_dotenv()

    router_host = os.environ["ROUTER_HOST"]
    router_password = os.environ["ROUTER_PASSWORD"]

    check_host = os.getenv("CHECK_HOST", "google.com")
    check_attempts = int(os.getenv("CHECK_ATTEMPTS", "3"))
    check_interval = int(os.getenv("CHECK_INTERVAL", "1"))
    check_retry_interval = int(os.getenv("CHECK_RETRY_INTERVAL", "10"))
    check_timeout = int(os.getenv("CHECK_TIMEOUT", "10"))

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    dry_run = os.getenv("DRY_RUN")

    log_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[log_handler]
    )

    logging.info("Will check [%s] every %d min", check_host, check_interval)
    logging.info("Will try %d times with %d s interval", check_attempts, check_retry_interval)
    logging.info("HTTP timeout is %d s", check_timeout)
    logging.info("Router is [%s], password is [%s]", router_host, "*" * len(router_password))
    logging.info("Logging with level %s", log_level)

    if dry_run:
        logging.info("Dry run mode")

    schedule.every(check_interval).minutes.do(check)

    while True:
        schedule.run_pending()
        sleep(1)
