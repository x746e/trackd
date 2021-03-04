from dataclasses import dataclass
from concurrent import futures
import datetime
import logging
import threading

from typing import Optional

import grpc
import tzlocal

import tmux
import tmux_pb2_grpc
import x11


@dataclass(frozen=True)
class Span:
    start: datetime.datetime
    end: datetime.datetime
    name: str

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name!r}, start={self.start}, end={self.end})'


def now() -> datetime.datetime:
    return datetime.datetime.now(tzlocal.get_localzone())


class SpanTracker:

    def __init__(self):
        self._active_span_name: Optional[str] = None
        self._active_span_start: Optional[datetime.datetime] = None

    def update_active_span(self, span_name: Optional[str]) -> None:
        if self._active_span_name == span_name:
            return

        if self._active_span_name is not None:
            self._emit()

        self._active_span_name = span_name
        self._active_span_start = now()

    def _emit(self) -> None:
        span = self._make_span()
        print(span)

    def _make_span(self) -> Span:
        assert self._active_span_name is not None
        assert self._active_span_start is not None
        return Span(
                start=self._active_span_start,
                end=now(),
                name=self._active_span_name,
        )


def main():
    logging.basicConfig()

    span_tracker = SpanTracker()
    tmux_adapter = tmux.TmuxAdapter(span_tracker)

    x_window_focus_tracker = x11.XWindowFocusTracker()
    x_window_focus_tracker.register(tmux_adapter.set_focused_x_window_id)
    x_thread = threading.Thread(target=x_window_focus_tracker.run, daemon=True)
    x_thread.start()

    servicer = tmux.Tmux(tmux_adapter)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tmux_pb2_grpc.add_TmuxServicer_to_server(servicer, server)
    server.add_insecure_port('[::]:3141')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
