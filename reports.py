
## Spans
# - output:
# == Tue, Mar 16
# 10:11   [nw] trackd (10m)
# 10:21   [w] iptables_audit (1h)

## Per day report
# == Tue, Mar 16:
# [w] iptables_audit   2h
# [w] chat             1h
# [w] meetings         3h
# [nw] trackd          30m
# == Wed, Mar 17
# ...

## Week report
# == Mar 15 -- Mar 21:
# [w] iptables_audit   20h
# [w] chat             10h


## Work hours report:
# = Mar 15 -- Mar 21:
# work hours: 30
# non-work hours: 10
#
# == Tue, Mar 16
# 09:00--10:15

from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
from pprint import pprint
import datetime
import os.path

from typing import Iterable, Optional

import click
import click_config_file

from time_utils import duration, humanize
import trackd
import chrome
import tmux


class SpanType(Enum):
    WORK = 1
    NON_WORK = 2


@dataclass(frozen=True)
class ReportSpan:
    """Represents a span in a more convenient format for reporting.

    Essentially processes tmux/chrome specific metadata into work/non-work distinction.
    """
    name: str
    type_: SpanType
    start: datetime.datetime
    end: datetime.datetime

    def __repr__(self):  # XXX: Make it __str__?
        type_ = '[w] ' if self.type_ is SpanType.WORK else '[nw]'
        duration = self.end - self.start
        return f'{type_} {str(self.name): <20} {duration} ({self.start} -- {self.end})'

    def length(self):
        return (self.end - self.start).total_seconds()


@dataclass(frozen=True)
class Options:
    hostname_work: str
    hostname_non_work: str
    chrome_user_work: str
    chrome_user_non_work: str


def split_work_non_work(opts: Options, raw_spans: Iterable[trackd.Span]) -> Iterable[ReportSpan]:
    """Transforms into work/non-work spans."""
    for span in raw_spans:
        if isinstance(span.session, tmux.TmuxSession):
            assert span.session.hostname in (opts.hostname_work, opts.hostname_non_work)
            if span.session.hostname == opts.hostname_work:
                type_ = SpanType.WORK
            elif span.session.hostname == opts.hostname_non_work:
                type_ = SpanType.NON_WORK
            else:
                raise RuntimeError(f'Unexpected hostname in TmuxSession: {span.session.hostname!r}')
        elif isinstance(span.session, chrome.ChromeSession):
            if span.session.user == opts.chrome_user_work:
                type_ = SpanType.WORK
            elif span.session.user == opts.chrome_user_non_work:
                type_ = SpanType.NON_WORK
            else:
                print(f'Unexpected user in ChromeSession: {span.session.user!r}')
                continue
        yield ReportSpan(
                name = span.session.session_name,
                type_ = type_,
                start = span.start,
                end = span.end,
        )


def merge(spans: Iterable[ReportSpan], n: int = 5) -> Iterable[ReportSpan]:
    """Merges same spans with end/start difference < n sec."""
    try:
        current = next(spans)
    except StopIteration:
        return

    try:
        while True:
            nxt = next(spans)
            if nxt.name != current.name or nxt.type_ != current.type_:
                yield current
                current = nxt
                continue
            if (nxt.start - current.end).total_seconds() <= n:
                current = ReportSpan(name=current.name, type_=current.type_,
                                     start=current.start, end=nxt.end)
            else:
                yield current
                current = nxt
    except StopIteration:
        yield current


def cull(spans: Iterable[ReportSpan], min_length: int = 3) -> Iterable[ReportSpan]:
    """Removes spans smaller than `min_length` seconds."""
    for span in spans:
        if not span.length() < min_length:
            yield span


def get_spans(opts: Options):
    span_storage = trackd.SpanStorage('spans.db')
    raw_spans = span_storage.query()
    spans = split_work_non_work(opts, raw_spans)
    spans = merge(spans)
    spans = cull(spans)
    return merge(spans)


def per_dey_report(opts: Options) -> None:

    min_length = duration('10m')

    def split_day(spans: Iterable[ReportSpan]) -> Iterable[ReportSpan]:
        """Splits a span going over midnight into two."""
        for span in spans:
            assert span.length() < duration('1d')

            if span.start.date() != span.end.date():
                second_start = span.end.replace(hour=0, second=0, minute=0, microsecond=0)
                assert second_start != span.end
                first_end = second_start - datetime.timedelta(microseconds=1)

                yield ReportSpan(name=span.name, type_=span.type_,
                                 start=span.start, end=first_end)
                yield ReportSpan(name=span.name, type_=span.type_,
                                 start=second_start, end=span.end)
            else:
                yield span


    @dataclass(frozen=True)
    class ReportKey:
        """Represents spans in time based reporting.

        Basically ReportSpan without start and end.
        """
        name: str
        type_: SpanType

        def __repr__(self):
            type_ = '[w] ' if self.type_ is SpanType.WORK else '[nw]'
            return f'{type_} {str(self.name): <20}'


    def make_key(span: ReportSpan) -> ReportKey:
        return ReportKey(name=span.name, type_=span.type_)


    spans = list(get_spans(opts))
    spans = split_day(spans)
    per_day = defaultdict(lambda: defaultdict(int))
    for span in spans:
        per_day[span.start.date()][make_key(span)] += span.length()

    for day, day_report in per_day.items():
        print(f'== {day:%a, %b %d}')
        itms = sorted(day_report.items(), key=lambda itm: itm[1], reverse=True)
        for k, length in itms:
            if length < min_length:
                continue
            print(k, humanize(length))



CONFIG_FILE = os.path.expanduser('~/trackctl.conf')

@click.group()
@click.option('--hostname_work', required=True)
@click.option('--hostname_non_work', required=True)
@click.option('--chrome_user_work', required=True)
@click.option('--chrome_user_non_work', required=True)
@click_config_file.configuration_option(config_file_name=CONFIG_FILE)
@click.pass_context
def cli(ctx, hostname_work, hostname_non_work, chrome_user_work, chrome_user_non_work):
    ctx.ensure_object(dict)
    ctx.obj['options'] = Options(hostname_work=hostname_work,
                                 hostname_non_work=hostname_non_work,
                                 chrome_user_work=chrome_user_work,
                                 chrome_user_non_work=chrome_user_non_work)


@cli.command()
@click.pass_context
def spans(ctx):
    opts = ctx.obj['options']
    spans = list(get_spans(opts))
    pprint(spans)


@cli.command()
@click.pass_context
def per_day(ctx):
    opts = ctx.obj['options']
    per_dey_report(opts)


if __name__ == '__main__':
    cli()
