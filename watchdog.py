#!/usr/bin/env python3

import logging
import os
import sys

import schedule

from dotenv import load_dotenv
from time import sleep
from urllib.request import urlopen

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

logging.info(f"Will check [{check_host}] once in {check_interval} min")
logging.info(f"Will attempt {check_attempts} times with {check_attempt_interval} s interval")
logging.info(f"Router is [{router_host}]")
logging.info(f"After reboot will delay for {post_reboot_delay} s")
logging.info(f"Logging with level {log_level}")

def wait_for_host(host, delay = 10, max_attempts = 1):
    remaining_attempts = max_attempts
    while True:
        try:
            urlopen(f"http://{host}")
            return True
        except:
            remaining_attempts -= 1
            if remaining_attempts > 0:
                logging.warning(f"Connection to {host} failed, will retry {remaining_attempts} more times")
                sleep(delay)
            else:
                logging.warning(f"{host} is unavailable")
                return False

def check():
    logging.debug(f"Checking {check_host}")
    if not wait_for_host(check_host, delay=check_attempt_interval, max_attempts=check_attempts):
        logging.warning("Rebooting router")
        router = ZTEAPI(router_host, router_password)
        router.login()
        router.reboot()
        sleep(post_reboot_delay)
        logging.info(f"Waiting for router {router_host}")
        wait_for_host(router_host, max_attempts=-1)
        logging.info(f"Router is up, resuming")
    logging.debug("Check successful")

schedule.every(check_interval).minutes.do(check)

while True:
    schedule.run_pending()
    sleep(1)
