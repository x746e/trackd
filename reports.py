
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
# == Tue, Mar 16
# 09:00--10:15

from dataclasses import dataclass
from enum import Enum
from pprint import pprint
import datetime
import os.path

from typing import Iterable, Optional

import click
import click_config_file

import trackd
import chrome
import tmux


class SpanType(Enum):
    WORK = 1
    NON_WORK = 2


@dataclass(frozen=True)
class ReportSpan:
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
    pprint(list(get_spans(ctx.obj['options'])))


if __name__ == '__main__':
    cli()
