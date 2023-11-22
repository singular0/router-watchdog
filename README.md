# Router Watchdog

This project was born from the despair of awful quality of service of certain UK 5G broadband
provider. Symptom of the problem that I have experienced is unavailability of internet service
manifesting as timeouts and connection errors on wi-fi and ethernet terminals while router
internal watchdog does not detect any anomalies.

Features:

* External watchdog that performs HTTP HEAD request and reboots router in case of consequent errors
* speedtest.net client that may measure bandwidth periodically
* Web UI with reboot and speed history graphs
* Simple REST API with statistics for displaying on Homepage

## Environment Variables

Variable               | Description
---------------------- | -----------
`DB_PATH`              | Optional. Path to SQLite file with check event history. Default is `router-watchdog.db`.
`DRY_RUN`              | Optional. If defined, no actual router reboot will happen.
`CHECK_HOST`           | Optional. Internet host name or address to perform HTTP `HEAD` request to. Default is `google.com`.
`CHECK_INTERVAL`       | Optional. Check interval in seconds. Default is `60`.
`CHECK_RETRY`          | Optional. Number of check retries before router will be rebooted. Default is `3`.
`CHECK_RETRY_INTERVAL` | Optional. Check retry interval in seconds. Default is `10`.
`CHECK_TIMEOUT`        | Optional. HTTP timeout for check requests in seconds. Default is `10`.
`LOG_LEVEL`            | Optional. Log level, one of [Python Logging Levels](https://docs.python.org/3/library/logging.html#levels). Default is `INFO`.
`SPEEDTEST_INTERVAL`   | Optional. Speedtest interval in seconds. Default is `3600` (1 hour).
`ZTE_ROUTER_HOST`      | ZTE router host name or address.
`ZTE_ROUTER_MODEL`     | Optional. ZTE router model: `MC801` or `MC888`. Default is `MC888`.
`ZTE_ROUTER_PASSWORD`  | ZTE router password.
`ZTE_ROUTER_USER`      | Optional. ZTE router username. Used only by MC888 model, default is `user`.

## Homepage Widget

```yaml
    - Router Watchdog:
        description: Reboots unresponsive router
        icon: router.png
        server: local
        container: router-watchdog
        href: http://192.168.0.1:8050/
        widget:
            type: customapi
            url: http://192.168.0.1:8050/stats
            refreshInterval: 60000
            mappings:
                - field: uptime
                  label: Uptime
                - field: reboots_today
                  label: Reboots Today
```
