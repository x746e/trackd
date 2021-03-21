from dataclasses import dataclass
import logging
import pprint
import threading

from typing import Optional

from google.protobuf import empty_pb2

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
class TmuxSession:
    """Tmux sessions are represented by tmux server PID + session name."""
    session_name: str
    hostname: str
    server_pid: int


class XWindowIdTmuxClientMap:
    """Maintains a mapping from a X Window ID to a tmux client.

    Thread-unsafe.
    """

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
        with self._lock:
            rpr = pprint.pformat({
                k.client_name: f'{v.hostname}:{v.session_name}'
                for k, v in self._map.items()
            })
            return f'{self.__class__.__name__}({rpr})'


class TmuxAdapter:

    def __init__(self, span_tracker):
        self._x_window_id_tmux_client_map = XWindowIdTmuxClientMap()
        self._tmux_client_session_map = TmuxClientSessionMap()
        self._lock = threading.Lock()
        self._span_tracker = span_tracker
        self._focused_x_window_id: Optional[x11.XWindowId] = None

    def _check_span(self):
        if self._focused_x_window_id not in self._x_window_id_tmux_client_map:
            self._span_tracker.update_active_session(None)
            return
        client = self._x_window_id_tmux_client_map[self._focused_x_window_id]

        if client not in self._tmux_client_session_map:
            self._span_tracker.update_active_session(None)
            return
        session = self._tmux_client_session_map[client]

        self._span_tracker.update_active_session(session)

    def set_focused_x_window_id(self, x_window_id: x11.XWindowId, window_name: str) -> None:
        # logging.debug('set_focused_x_window_id(%r, %r)', x_window_id, window_name)
        with self._lock:
            self._focused_x_window_id = x_window_id
            self._check_span()

    ##
    # Methods for maintaining X Window ID ↔ tmux client mapping.

    def set_client_for_x_window_id(self, x_window_id: x11.XWindowId, client: TmuxClient) -> None:
        logging.debug('set_client_for_x_window_id(%r, %r)', x_window_id, client)
        with self._lock:
            self._x_window_id_tmux_client_map[x_window_id] = client
            # TODO: At this point the client shouldn't have a corresponding TmuxSession.
            # If it does we should raise a "surprise alert" here.
            self._check_span()

    def clear_client_for_x_window_id(self, x_window_id: x11.XWindowId) -> None:
        logging.debug('clear_client_for_x_window_id(%r)', x_window_id)
        with self._lock:
            try:
                client = self._x_window_id_tmux_client_map[x_window_id]
            except KeyError:
                pass
            else:
                del self._x_window_id_tmux_client_map[x_window_id]
                # The client will also be detached from any sessions.
                try:
                    del self._tmux_client_session_map[client]
                except KeyError:
                    pass
            self._check_span()

    ##
    # Methods for maintaining tmux client ↔ session mapping.

    def client_session_changed(self, client: TmuxClient, session: TmuxSession) -> None:
        logging.debug('client_session_changed(%r, %r)', client, session)
        with self._lock:
            self._tmux_client_session_map[client] = session
            self._check_span()

    def client_detached(self, client: TmuxClient) -> None:
        logging.debug('client_detached(%r)', client)
        with self._lock:
            try:
                del self._tmux_client_session_map[client]
            except KeyError:
                pass
            self._check_span()

    def session_renamed(self, client: TmuxClient, new_session: TmuxSession) -> None:
        logging.debug('session_renamed(%r, %r)', client, new_session)
        with self._lock:
            self._tmux_client_session_map.session_renamed(client, new_session)
            self._check_span()

    def session_closed(self, session: TmuxSession) -> None:
        logging.debug('session_closed(%r)', session)
        with self._lock:
            self._tmux_client_session_map.session_closed(session)
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
