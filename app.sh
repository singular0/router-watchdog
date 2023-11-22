#!/bin/sh

python3 -m watchdog.services.watchdog &

python3 server.py
