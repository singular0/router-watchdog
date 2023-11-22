"""Human readable formatting functions."""

from datetime import timedelta


def time_interval(value: int | timedelta, *, short: bool = False) -> str:
    """
    Return human readable interval.

    Parameters:
        value (int | timedelta): interval value
        short (bool): use abbreviation of time units

    Returns:
        (str): human readable interval

    Raises:
        TypeError: in case unsupported type passed as interval
    """
    if type(value) == timedelta:
        sec = int(value.total_seconds())
    elif type(value) == int:
        sec = value
    else:
        raise TypeError('interval must be either int or timedelta')
    min = int(sec / 60)
    sec = int(sec % 60)
    hour = int(min / 60)
    min = int(min % 60)
    if hour < 24:
        return f'{hour:}:{min:02}:{sec:02}'
    day = int(hour / 24)
    hour = int(hour % 24)
    day_unit = 'd' if short else ' day'
    if day > 1:
        day_unit += 's'
    return f'{day:}{day_unit} {hour:02}:{min:02}'


def speed(value: float) -> str:
    """
    Return human readable speed value.

    Parameters:
        value (float): speed in bps

    Returns:
        (str): human readable speed value
    """
    if value < 8000:
        return f"{value:.0f} B/s"
    elif value < 8000000:
        return f"{value / 8000:.0f} kB/s"
    elif value < 8000000000:
        return f"{value / 8000000:.1f} MB/s"
    else:
        return f"{value / 8000000000:.2f} GB/s"
