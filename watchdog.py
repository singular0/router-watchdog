#!/usr/bin/env python3

"""Watchdog process."""

import logging
import os
import sys

from db import DB

from devices.zte_router import ZTERouter

from dotenv import load_dotenv

from requests import RequestException

from services.watchdog import Watchdog, WatchdogEvent


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
