#!/usr/bin/env python3

""" Router watchdog """

import logging
import os
import sys

from time import sleep
from urllib.request import urlopen
from urllib.error import HTTPError

import schedule

from dotenv import load_dotenv

from zte_api import ZTEAPI

load_dotenv()

router_host = os.environ['ROUTER_HOST']
router_password = os.environ['ROUTER_PASSWORD']

check_interval = int(os.getenv("CHECK_INTERVAL", "1"))
check_host = os.getenv("CHECK_HOST", "google.com")
check_attempts = int(os.getenv("CHECK_ATTEMPTS", "3"))
check_attempt_interval = int(os.getenv("CHECK_ATTEMPT_INTERVAL", "10"))

post_reboot_delay = int(os.getenv("POST_REBOOT_DELAY", "10"))

log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

log_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[log_handler]
)

logging.info("Will check [%s] once in %d min", check_host, check_interval)
logging.info("Will attempt %d times with %d s interval", check_attempts, check_attempt_interval)
logging.info("Router is [%s]", router_host)
logging.info("After reboot will delay for %d s", post_reboot_delay)
logging.info("Logging with level %s", log_level)

def wait_for_host(host, delay = 10, max_attempts = 1):
    """ Wait for the host to respond to a HTTP request without errors """
    remaining_attempts = max_attempts
    while True:
        try:
            urlopen(f"http://{host}")
            return True
        except HTTPError:
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
    logging.debug("Checking %s", check_host)
    if not wait_for_host(check_host, delay=check_attempt_interval, max_attempts=check_attempts):
        while True:
            try:
                logging.warning("Rebooting router")
                router = ZTEAPI(router_host, router_password)
                router.login()
                router.reboot()
                sleep(post_reboot_delay)
                logging.info("Waiting for router %s", router_host)
                wait_for_host(router_host, max_attempts=-1)
                logging.info("Router is up, resuming")
                break
            except ConnectionError:
                logging.error("Router unavailable while rebooting, will retry in %d s",
                              check_attempt_interval)
                sleep(check_attempt_interval)
    else:
        logging.debug("Check successful")

schedule.every(check_interval).minutes.do(check)

while True:
    schedule.run_pending()
    sleep(1)
