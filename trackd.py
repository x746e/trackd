from concurrent import futures
from dataclasses import dataclass
import datetime
import logging
import pprint
import threading

from typing import Optional

from google.protobuf import empty_pb2
import grpc
import tzlocal

import tmux_pb2
import tmux_pb2_grpc
import x11


@dataclass(frozen=True)
class TmuxClient:
    """Tmux clients are represented by hostname + client name.

    Client name happens to be a tty name.
    """
    hostname: str
    client_name: str


@dataclass(frozen=True)
class Session:
    session_name: str


@dataclass(frozen=True)
class TmuxSession(Session):
    """Tmux sessions are represented by tmux server PID + session name."""
    hostname: str
    server_pid: int


@dataclass(frozen=True)
class ChromeSession(Session):
    pass


# TODO: Rename to XWindowTmuxClientMap
class TmuxClientXWindowIdMap:
    """Maintains a mapping from a X Window ID to a tmux client."""

    def __init__(self):
        self._map = {}

    def __getitem__(self, x_window_id: x11.XWindowId) -> TmuxClient:
        return self._map[x_window_id]

    def __setitem__(self, x_window_id: x11.XWindowId, client: TmuxClient) -> None:
        self._map[x_window_id] = client

    def __delitem__(self, x_window_id: x11.XWindowId) -> None:
        del self._map[x_window_id]

    def __contains__(self, x_window_id: x11.XWindowId) -> bool:
        return x_window_id in self._map

    def __repr__(self):
        rpr = pprint.pformat({
            k: f'{v.hostname}:{v.client_name}'
            for k, v in self._map.items()
        })
        return f'{self.__class__.__name__}({rpr})'


class TmuxClientSessionMap:
    """Maintains a mapping from a tmux client to a tmux session."""

    def __init__(self):
        self._map = {}
        self._lock = threading.Lock()

    def __getitem__(self, client: TmuxClient) -> TmuxSession:
        with self._lock:
            return self._map[client]

    def __setitem__(self, client: TmuxClient, session: TmuxSession) -> None:
        with self._lock:
            self._map[client] = session

    def __delitem__(self, client: TmuxClient) -> None:
        with self._lock:
            del self._map[client]

    def __contains__(self, client: TmuxClient) -> bool:
        with self._lock:
            return client in self._map

    def session_renamed(self, client: TmuxClient, new_session: TmuxSession) -> None:
        with self._lock:
            # * Find the name of the session the client is connected to
            #   according to our data.
            old_session = self._map[client]
            # * Find if there are any other clients on that hostname connected
            #   to the same session on the same tmux server.
            clients_to_update = [
                    client
                    for client, session in self._map.items()
                    if session == old_session
            ]
            # * For each client set it to the new session
            for client in clients_to_update:
                self._map[client] = new_session

    def session_closed(self, session: TmuxSession) -> None:
        with self._lock:
            clients_to_update = [
                    client
                    for client, session_ in self._map.items()
                    if session_ == session
            ]
            for client in clients_to_update:
                del self._map[client]

    def __repr__(self):
        rpr = pprint.pformat({
            k.client_name: f'{v.hostname}:{v.session_name}'
            for k, v in self._map.items()
        })
        return f'{self.__class__.__name__}({rpr})'


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
        assert self._active_span_name is not None
        assert self._active_span_start is not None
        span = Span(
                start=self._active_span_start,
                end=now(),
                name=self._active_span_name,
        )
        print(span)


class TmuxAdapter:

    def __init__(self, span_tracker: SpanTracker):
        self._tmux_client_x_window_id_map = TmuxClientXWindowIdMap()
        self._tmux_client_session_map = TmuxClientSessionMap()
        self._lock = threading.Lock()
        self._span_tracker = span_tracker
        self._focused_x_window_id: Optional[x11.XWindowId] = None

    def set_focused_x_window_id(self, x_window_id: x11.XWindowId) -> None:
        with self._lock:
            print(f'set_focused_x_window_id({x_window_id})')
            self._focused_x_window_id = x_window_id
            self._check_span()

    def _check_span(self):
        if self._focused_x_window_id not in self._tmux_client_x_window_id_map:
            self._span_tracker.update_active_span(None)
            return
        client = self._tmux_client_x_window_id_map[self._focused_x_window_id]

        if client not in self._tmux_client_session_map:
            self._span_tracker.update_active_span(None)
            return
        session = self._tmux_client_session_map[client]

        print('_check_span:', session)
        self._span_tracker.update_active_span(session.session_name)

    ##
    # Methods for maintaining X Window ID ↔ tmux client mapping.

    def set_client_for_x_window_id(self, x_window_id: x11.XWindowId, client: TmuxClient) -> None:
        with self._lock:
            self._tmux_client_x_window_id_map[x_window_id] = client
            print(self._tmux_client_x_window_id_map)
            self._check_span()

    def clear_client_for_x_window_id(self, x_window_id: x11.XWindowId) -> None:
        with self._lock:
            try:
                client = self._tmux_client_x_window_id_map[x_window_id]
            except KeyError:
                pass
            else:
                del self._tmux_client_x_window_id_map[x_window_id]
                # The client will also be detached from any sessions.
                try:
                    del self._tmux_client_session_map[client]
                except KeyError:
                    pass
            print(self._tmux_client_x_window_id_map)
            print(self._tmux_client_session_map)
            self._check_span()

    ##
    # Methods for maintaining tmux client ↔ session mapping.

    def client_session_changed(self, client: TmuxClient, session: TmuxSession) -> None:
        with self._lock:
            self._tmux_client_session_map[client] = session
            print(self._tmux_client_session_map)
            self._check_span()

    def client_detached(self, client: TmuxClient) -> None:
        with self._lock:
            print('tmux_client_detached:', client)

            try:
                del self._tmux_client_session_map[client]
            except KeyError:
                pass
            print(self._tmux_client_session_map)
            self._check_span()

    def session_renamed(self, client: TmuxClient, new_session: TmuxSession) -> None:
        with self._lock:
            self._tmux_client_session_map.session_renamed(client, new_session)
            print(self._tmux_client_session_map)
            self._check_span()

    def session_closed(self, session: TmuxSession) -> None:
        with self._lock:
            print('tmux_session_closed:', session)

            self._tmux_client_session_map.session_closed(session)
            print(self._tmux_client_session_map)
            self._check_span()


class Tmux(tmux_pb2_grpc.TmuxServicer):
    """A Tmux gRPC server.

    Passes updates from shell and tmux to TmuxController.
    """

    def __init__(self, tmux_adapter: TmuxAdapter):
        self._tmux_adapter = tmux_adapter

    def set_client_for_x_window_id(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        self._tmux_adapter.set_client_for_x_window_id(request.x_window_id, client)
        return empty_pb2.Empty()

    def clear_client_for_x_window_id(self, request, context):
        self._tmux_adapter.clear_client_for_x_window_id(request.x_window_id)
        return empty_pb2.Empty()

    def client_session_changed(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        session = TmuxSession(hostname=request.hostname,
                              server_pid=request.server_pid,
                              session_name=request.session_name)
        self._tmux_adapter.client_session_changed(client, session)

        return empty_pb2.Empty()

    def client_detached(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        self._tmux_adapter.client_detached(client)
        return empty_pb2.Empty()

    def session_renamed(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        new_session = TmuxSession(hostname=request.hostname,
                                  server_pid=request.server_pid,
                                  session_name=request.new_session_name)
        self._tmux_adapter.session_renamed(client, new_session)
        return empty_pb2.Empty()

    def session_closed(self, request, context):
        session = TmuxSession(hostname=request.hostname,
                              server_pid=request.server_pid,
                              session_name=request.session_name)
        self._tmux_adapter.session_closed(session)
        return empty_pb2.Empty()


def main():
    logging.basicConfig()

    span_tracker = SpanTracker()
    tmux_adapter = TmuxAdapter(span_tracker)

    x_window_focus_tracker = x11.XWindowFocusTracker()
    x_window_focus_tracker.register(tmux_adapter.set_focused_x_window_id)
    x_thread = threading.Thread(target=x_window_focus_tracker.run, daemon=True)
    x_thread.start()

    servicer = Tmux(tmux_adapter)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tmux_pb2_grpc.add_TmuxServicer_to_server(servicer, server)
    server.add_insecure_port('[::]:3141')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
