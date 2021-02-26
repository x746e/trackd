from concurrent import futures
from dataclasses import dataclass
import logging
import pprint
import threading

import grpc
from google.protobuf import empty_pb2
import tmux_pb2
import tmux_pb2_grpc


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
    hostname: str
    server_pid: int
    session_name: str


XWindowId = int


class TmuxClientXWindowIdMap:
    """Maintains a mapping from a X Window ID to a tmux client."""

    def __init__(self):
        self._map = {}

    def __getitem__(self, x_window_id: XWindowId) -> TmuxClient:
        return self._map[x_window_id]
    
    def __setitem__(self, x_window_id: XWindowId, client: TmuxClient) -> None:
        self._map[x_window_id] = client

    def __delitem__(self, x_window_id: XWindowId) -> None:
        del self._map[x_window_id]

    def __contains__(self, x_window_id: XWindowId) -> bool:
        return x_window_id in self._map

    def __repr__(self):
        rpr = pprint.pformat({
            k: v.client_name
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
            k.client_name: v.session_name
            for k, v in self._map.items()
        })
        return f'{self.__class__.__name__}({rpr})'


class Tmux(tmux_pb2_grpc.TmuxServicer):

    def __init__(self, tmux_client_x_window_id_map, tmux_client_session_map):
        self._tmux_client_x_window_id_map = tmux_client_x_window_id_map
        self._tmux_client_session_map = tmux_client_session_map

    ##
    # Methods for maintaining X Window ID ↔ tmux client mapping.

    def set_client_for_x_window_id(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        self._tmux_client_x_window_id_map[request.x_window_id] = client
        print(self._tmux_client_x_window_id_map)
        return empty_pb2.Empty()

    def clear_client_for_x_window_id(self, request, context):
        try:
            del self._tmux_client_x_window_id_map[request.x_window_id]
        except KeyError:
            pass
        # The client will also be detached from any sessions.
        try:
            del self._tmux_client_session_map[client]
        except KeyError:
            pass
        print(self._tmux_client_x_window_id_map)
        print(self._tmux_client_session_map)
        return empty_pb2.Empty()

    ##
    # Methods for maintaining tmux client ↔ session mapping.

    def client_session_changed(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        session = TmuxSession(hostname=request.hostname,
                              server_pid=request.server_pid,
                              session_name=request.session_name)

        self._tmux_client_session_map[client] = session
        print(self._tmux_client_session_map)
        return empty_pb2.Empty()

    def client_detached(self, request, context):
        client = TmuxClient(hostname=data['hostname'],
                            client_name=data['client_name'])
        print('tmux_client_detached:', client)

        try:
            del self._tmux_client_session_map[client]
        except KeyError:
            pass
        print(self._tmux_client_session_map)
        return empty_pb2.Empty()

    def session_renamed(self, request, context):
        client = TmuxClient(hostname=request.hostname,
                            client_name=request.client_name)
        new_session = TmuxSession(hostname=request.hostname,
                                  server_pid=request.server_pid,
                                  session_name=request.new_session_name)

        self._tmux_client_session_map.session_renamed(client, new_session)
        print(self._tmux_client_session_map)
        return empty_pb2.Empty()

    def session_closed(self, request, context):
        session = TmuxSession(hostname=request.hostname,
                              server_pid=request.server_pid,
                              session_name=request.session_name)
        print('tmux_session_closed:', session)

        self._tmux_client_session_map.session_closed(session)
        print(self._tmux_client_session_map)
        return empty_pb2.Empty()


def main():
    logging.basicConfig()

    tmux_client_x_window_id_map = TmuxClientXWindowIdMap()
    tmux_client_session_map = TmuxClientSessionMap()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tmux_pb2_grpc.add_TmuxServicer_to_server(
            Tmux(
                tmux_client_x_window_id_map,
                tmux_client_session_map,
            ),
            server
    )
    server.add_insecure_port('[::]:3141')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    main()
