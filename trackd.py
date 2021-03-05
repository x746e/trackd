from dataclasses import dataclass
from concurrent import futures
import datetime
import logging
import pathlib
import sqlite3
import threading

from typing import Iterable, Optional

import absl.logging
import grpc
import tzlocal

import chrome
import tmux
import tmux_pb2_grpc
import x11


@dataclass(frozen=True)
class Span:
    span_name: str
    start: datetime.datetime
    end: datetime.datetime

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.span_name!r}, start={self.start}, end={self.end})'


def now() -> datetime.datetime:
    return datetime.datetime.now(tzlocal.get_localzone())


class SpanTracker:

    def __init__(self, span_storage: 'SpanStorage'):
        self._active_span_name: Optional[str] = None
        self._active_span_start: Optional[datetime.datetime] = None
        self._span_storage = span_storage

    def update_active_span(self, span_name: Optional[str]) -> None:
        if self._active_span_name == span_name:
            return

        if self._active_span_name is not None:
            self._emit()

        self._active_span_name = span_name
        self._active_span_start = now()

    def _emit(self) -> None:
        span = self._make_span()
        self._span_storage.add(span)

    def _make_span(self) -> Span:
        assert self._active_span_name is not None
        assert self._active_span_start is not None
        return Span(
                start=self._active_span_start,
                end=now(),
                span_name=self._active_span_name,
        )


class SpanStorage:

    def __init__(self, db_path: str):
        self._connect(db_path)
        self._lock = threading.Lock()

    def _connect(self, db_path: str) -> None:
        do_init = db_path == ':memory:' or not pathlib.Path(db_path).exists()
        self._conn = sqlite3.connect(
                db_path, detect_types=sqlite3.PARSE_DECLTYPES,  check_same_thread=False)

        if do_init:
            self._init_db()

    def _init_db(self) -> None:
        c = self._conn.cursor()
        c.execute("""
        CREATE TABLE spans (
            span_name text,
            start timestamp,
            end timestamp
        )
        """)
        self._conn.commit()

    def add(self, span: Span) -> None:
        with self._lock:
            c = self._conn.cursor()
            c.execute("""
                INSERT INTO spans (
                    span_name,
                    start,
                    end
                ) VALUES (
                    ?,
                    ?,
                    ?
                )
            """, (span.span_name,
                span.start.astimezone(datetime.timezone.utc),
                span.end.astimezone(datetime.timezone.utc)))
            self._conn.commit()

    def query(self) -> Iterable[Span]:
        c = self._conn.cursor()
        for row in c.execute("SELECT span_name, start, end FROM spans"):
            span_name, start, end = row
            # TODO: Do these data manipulations in converters and adapters.
            start = start.replace(tzinfo=datetime.timezone.utc)
            start = start.astimezone(tzlocal.get_localzone())
            end = end.replace(tzinfo=datetime.timezone.utc)
            end = end.astimezone(tzlocal.get_localzone())
            yield Span(span_name=span_name, start=start, end=end)


def main():
    handler = logging.StreamHandler()
    handler.setFormatter(absl.logging.PythonFormatter())
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)

    span_storage = SpanStorage('spans.db')
    span_tracker = SpanTracker(span_storage)

    chrome_servicer = chrome.Chrome(span_tracker)
    chrome_thread = threading.Thread(target=chrome.serve, args=(chrome_servicer,), daemon=True)
    chrome_thread.start()

    tmux_adapter = tmux.TmuxAdapter(span_tracker)

    x_window_focus_tracker = x11.XWindowFocusTracker()
    x_window_focus_tracker.register(tmux_adapter.set_focused_x_window_id)
    x_thread = threading.Thread(target=x_window_focus_tracker.run, daemon=True)
    x_thread.start()

    tmux_servicer = tmux.Tmux(tmux_adapter)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tmux_pb2_grpc.add_TmuxServicer_to_server(tmux_servicer, server)
    server.add_insecure_port('[::]:3141')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
