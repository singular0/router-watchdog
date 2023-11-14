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
