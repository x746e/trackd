from collections import namedtuple
from datetime import timedelta
import re

from typing import Tuple, Union

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
    '2d20h2m3s'
    >>> humanize(duration('20h2m3s'))
    '20h2m3s'
    """
    days, hours, minutes, seconds = _split_seconds(interval)

    ret = ''
    if days:
        ret += '%dd' % days
    if hours:
        ret += '%dh' % hours
    if minutes:
        ret += '%dm' % minutes
    if seconds:
        ret += '%ds' % seconds
    return ret


def hours(interval: Union[timedelta, int], unicode_=True) -> str:
    """Rounds up `interval` in seconds to hours.

    >>> hours(duration('24s'))
    '0h'
    >>> hours(duration('7m'))
    '0h'
    >>> hours(duration('8m'))
    '¼h'
    >>> hours(duration('13m'))
    '¼h'
    >>> hours(duration('15m'))
    '¼h'
    >>> hours(duration('16m'))
    '¼h'
    >>> hours(duration('18m'))
    '¼h'
    >>> hours(duration('20m'))
    '¼h'
    >>> hours(duration('25m'))
    '½h'
    >>> hours(duration('1h25m'))
    '1½h'
    >>> hours(duration('1h30m'))
    '1½h'
    >>> hours(duration('1h35m'))
    '1½h'
    >>> hours(duration('1h40m'))
    '1¾h'
    >>> hours(duration('2h'))
    '2h'
    >>> hours(duration('3d'))
    '3d'
    >>> hours(duration('2d20h'))
    '2d20h'
    >>> hours(duration('2d20h2m3s'))
    '2d20h'
    >>> hours(duration('20h2m3s'))
    '20h'
    """
    if isinstance(interval, timedelta):
        interval = int(interval.total_seconds())

    days, hours, minutes, seconds = _split_seconds(interval)

    ret = ''
    if days:
        ret += f'{days}d'

    quarters = round(minutes / 15)
    if quarters == 4:
        hours += 1
        minutes_str = ''
    elif quarters == 3:
        minutes_str = '¾' if unicode_ else '3/4'
    elif quarters == 2:
        minutes_str = '½' if unicode_ else '1/2'
    elif quarters == 1:
        minutes_str = '¼' if unicode_ else '1/4'
    elif quarters == 0:
        minutes_str = ''
    else:
        raise AssertionError(f'`quarters=={quarters}` are out of bound')

    if hours:
        ret += str(hours)
        if minutes_str and not unicode_:
            ret += ' '
    if minutes_str:
        ret += minutes_str
    if not (days or hours or minutes_str):
        return '0h'
    if hours or minutes_str:
        ret += 'h'
    return ret



TimeParts = namedtuple('TimeParts', 'days hours minutes seconds')


def _split_seconds(interval: Union[timedelta, int]) -> TimeParts:
    if isinstance(interval, timedelta):
        interval = int(interval.total_seconds())
    else:
        interval = int(interval)

    days = interval // duration('1d')
    interval %= duration('1d')
    hours = interval // duration('1h')
    interval %= duration('1h')
    minutes = interval // duration('1m')
    interval %= duration('1m')
    seconds = int(interval)

    return TimeParts(days, hours, minutes, seconds)
