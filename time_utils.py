from datetime import timedelta
import re

from typing import Union

UNITS = {
    's': 'seconds',
    'm': 'minutes',
    'h': 'hours',
    'd': 'days',
    'w': 'weeks',
}


def duration(s: str) -> int:
    """Parses time strings, like "2h30m24s", into number of seconds.

    >>> duration('24s')
    24
    >>> duration('1m')
    60
    >>> duration('1d')
    86400
    """
    delta = timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): int(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+)(?P<unit>[smhdw]?)', s, flags=re.I)
    })
    return int(delta.total_seconds())


def humanize(interval: Union[timedelta, int]) -> str:
    """Converts time interval into a string like "2h30m".

    TODO: Used in reports, so it doesn't bother too much with preciseness, and rounds up to ~¼h.

    >>> humanize(duration('24s'))
    '24s'
    >>> humanize(duration('20m'))
    '20m'
    >>> humanize(duration('2h'))
    '2h'
    >>> humanize(duration('3d'))
    '3d'
    >>> humanize(duration('2d20h'))
    '2d20h'
    >>> humanize(duration('2d20h2m3s'))
    '2d20h'
    >>> humanize(duration('20h2m3s'))
    '20h2m'
    """
    if isinstance(interval, timedelta):
        interval = int(interval.total_seconds())

    days = interval // duration('1d')
    interval %= duration('1d')
    hours = interval // duration('1h')
    interval %= duration('1h')
    minutes = interval // duration('1m')
    interval %= duration('1m')
    seconds = int(interval)

    ret = ''
    if days:
        ret += '%dd' % days
    if hours:
        ret += '%dh' % hours
    if minutes and not days:
        ret += '%dm' % minutes
    if seconds and not days and not hours:
        ret += '%ds' % seconds
    return ret
