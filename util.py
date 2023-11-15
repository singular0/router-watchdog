"""Utility functions."""


def diff_times(time1: int, time2: int) -> str:
    """
    Return human readable difference between two timestamps.

    Parameters:
        time1 (int): timestamp 1
        time2 (int): timestamp 2

    Returns:
        (str): human readable difference
    """
    sec = time1 - time2
    min = int(sec / 60)
    sec = int(sec % 60)
    hour = int(min / 60)
    min = int(min % 60)
    if hour < 24:
        return f'{hour:02}:{min:02}'
    day = int(hour / 24)
    hour = int(hour % 24)
    s = 's' if day > 1 else ''
    return f'{day:} day{s} {hour:02}:{min:02}'


def format_speed(value: float) -> str:
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
