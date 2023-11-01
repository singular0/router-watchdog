#!/usr/bin/env python3

"""Router watchdog."""

import logging
import os
import sys

from db import DB

from dotenv import load_dotenv

from ui import UI

from watchdog import Watchdog


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

    db = DB(db_path=db_path)

    watchdog = Watchdog(check_host=check_host, check_retries=check_retry,
                        check_timeout=check_timeout, check_interval=check_interval,
                        retry_interval=check_retry_interval, dry_run=dry_run,
                        router_host=router_host, router_password=router_password,
                        db=db)
    watchdog.start()

    ui = UI(db=db)
    ui.start()
