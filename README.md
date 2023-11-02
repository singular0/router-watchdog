# Environment Variables

Variable               | Description
---------------------- | -----------
`ROUTER_HOST`          | ZTE router host name or address.
`ROUTER_PASSWORD`      | Router admin password.
`CHECK_HOST`           | Optional. Internet host name or address to perform HTTP `HEAD` request to. Default is `google.com`.
`CHECK_INTERVAL`       | Optional. Check interval in seconds. Default is `60`.
`CHECK_RETRY`          | Optional. Number of check retries before router will be rebooted. Default is `3`.
`CHECK_RETRY_INTERVAL` | Optional. Check retry interval in seconds. Default is `10`.
`CHECK_TIMEOUT`        | Optional. HTTP timeout for check requests in seconds. Default is `10`.
`DB_PATH`              | Optional. Path to SQLite file with check event history. Default is `router-watchdog.db`.
`LOG_LEVEL`            | Optional. Log level, one of [Python Logging Levels](https://docs.python.org/3/library/logging.html#levels). Default is `INFO`.
`DRY_RUN`              | If defined, no actual router reboot will happen.

# Homepage Widget

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
            mappings:
                - field: uptime
                  label: Uptime
```
