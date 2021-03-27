## Text calendar
# == Tue, Mar 16
# 08:00  iptables_audit [30m]
# 08:30  iptables_audit [20m], chat [5m]
# 09:00
# 09:30
# 10:00

from dataclasses import dataclass
from collections import defaultdict
from enum import Enum
from pprint import pprint
import datetime
import os.path

from typing import Iterable, Optional, Union

import click
import click_config_file

from time_utils import duration, hours, humanize
import trackd
import chrome
import tmux


@dataclass(frozen=True)
class Options:
    # How to convert tmux/chrome metadata into work/non-work.
    hostname_work: str
    hostname_non_work: str
    chrome_user_work: str
    chrome_user_non_work: str
    # Don't report spans sum of which is shorter than this.
    min_length: int

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
        duration = datetime.timedelta(seconds=int(duration.total_seconds()))
        return f'{self.start:%H:%M:%S}-{self.end:%H:%M:%S} {type_} {self.name: <20} {duration}'

    def length(self):
        return int((self.end - self.start).total_seconds())


@dataclass(frozen=True)
class ReportKey:
    """Represents spans in time based reporting.

    Basically ReportSpan without start and end.
    """
    name: str
    type_: SpanType

    def __repr__(self):
        type_ = '[w] ' if self.type_ is SpanType.WORK else '[nw]'
        return f'{type_} {self.name: <20}'


def split_work_non_work(opts: Options,
                        raw_spans: Iterable[trackd.Span]) -> Iterable[ReportSpan]:
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
                name = str(span.session.session_name),
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


def cull(spans: Iterable[ReportSpan], min_length: int = 5) -> Iterable[ReportSpan]:
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


def spans_report(opts: Options):
    current_day = None
    for span in get_spans(opts):
        if span.start.date() != current_day:
            current_day = span.start.date()
            print(f'== {current_day:%a, %b %d}')
        print(span)
        # print(f'{span.start:%H:%M} {span.name: <}')


def per_day_report(opts: Options) -> None:

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

    def make_key(span: ReportSpan) -> ReportKey:
        return ReportKey(name=span.name, type_=span.type_)

    spans = list(get_spans(opts))
    spans = split_day(spans)
    per_day_per_w_nw = defaultdict(lambda: defaultdict(int))
    per_day_per_project = defaultdict(lambda: defaultdict(int))
    workday_start = {}
    workday_end = {}
    for span in spans:
        per_day_per_w_nw[span.start.date()][span.type_] += span.length()
        per_day_per_project[span.start.date()][make_key(span)] += span.length()
        if span.type_ == SpanType.WORK and span.length() >= opts.min_length:
            day = span.start.date()
            if day not in workday_start:
               workday_start[day] = span.start.time()
            if day not in workday_end or span.end.time() > workday_end[day]:
                workday_end[day] = span.end.time()

    for day, day_report in per_day_per_project.items():
        print(f'\n== {day:%a, %b %d}')
        work_hours = hours(per_day_per_w_nw[day][SpanType.WORK])
        non_work_hours = hours(per_day_per_w_nw[day][SpanType.NON_WORK])
        print(f'Σ: w={work_hours}, nw={non_work_hours}')
        if day in workday_start:
            assert day in workday_end
            day_start = workday_start[day].strftime('%H:%M')
            day_end = workday_end[day].strftime('%H:%M')
            print(f'work day: {day_start}—{day_end}')
        print()
        itms = sorted(day_report.items(), key=lambda itm: itm[1], reverse=True)
        for k, length in itms:
            if length < opts.min_length:
                continue
            print(k, hours(length))


def per_week_report(opts: Options) -> None:

    def get_week(dt: Union[datetime.datetime, datetime.date]) -> int:
        _, week, _ = dt.isocalendar()
        return week

    def format_week(week: int) -> str:
        # XXX TODO: Take the year out of actual spans.
        # I won't need it before 2022 though.
        year = datetime.datetime.now().year
        week_start = datetime.date.fromisocalendar(year, week, day=1)
        week_end = datetime.date.fromisocalendar(year, week, day=7)
        return f'{week_start:%b %d} — {week_end:%b %d}'

    def split_week(spans: Iterable[ReportSpan]) -> Iterable[ReportSpan]:
        """Splits a span going over Sunday → Monday midnight into two."""
        for span in spans:
            assert span.length() < duration('7d')
            if get_week(span.start) != get_week(span.end):
                raise NotImplementedError
            yield span

    def make_key(span: ReportSpan) -> ReportKey:
        return ReportKey(name=span.name, type_=span.type_)

    spans = list(get_spans(opts))
    spans = split_week(spans)
    per_week_per_w_nw = defaultdict(lambda: defaultdict(int))
    per_week_per_project = defaultdict(lambda: defaultdict(int))
    for span in spans:
        per_week_per_w_nw[get_week(span.start)][span.type_] += span.length()
        per_week_per_project[get_week(span.start)][make_key(span)] += span.length()

    for week, week_report in per_week_per_project.items():
        print(f'\n== {format_week(week)}')
        work_hours = hours(per_week_per_w_nw[week][SpanType.WORK])
        non_work_hours = hours(per_week_per_w_nw[week][SpanType.NON_WORK])
        print(f'Σ: w={work_hours}, nw={non_work_hours}')
        print()
        itms = sorted(week_report.items(), key=lambda itm: itm[1], reverse=True)
        for k, length in itms:
            if length < opts.min_length:
                continue
            print(k, hours(length))


CONFIG_FILE = os.path.expanduser('~/trackctl.conf')

@click.group()
@click.option('--hostname_work', required=True)
@click.option('--hostname_non_work', required=True)
@click.option('--chrome_user_work', required=True)
@click.option('--chrome_user_non_work', required=True)
@click.option('--min_length', required=True,
              help="Don't report spans sum of which is shorter than this.",
              default=duration('7m'))
@click_config_file.configuration_option(config_file_name=CONFIG_FILE)
@click.pass_context
def cli(ctx, hostname_work, hostname_non_work, chrome_user_work, chrome_user_non_work, min_length):
    ctx.ensure_object(dict)
    ctx.obj['options'] = Options(
            hostname_work=hostname_work,
            hostname_non_work=hostname_non_work,
            chrome_user_work=chrome_user_work,
            chrome_user_non_work=chrome_user_non_work,
            min_length=min_length)


@cli.command()
@click.pass_context
def spans(ctx):
    opts = ctx.obj['options']
    spans_report(opts)


@cli.command()
@click.pass_context
def per_day(ctx):
    opts = ctx.obj['options']
    per_day_report(opts)


@cli.command()
@click.pass_context
def per_week(ctx):
    opts = ctx.obj['options']
    per_week_report(opts)


if __name__ == '__main__':
    cli()
