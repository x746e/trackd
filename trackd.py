from dataclasses import dataclass
from pprint import pprint
import threading

import flask


app = flask.Flask(__name__)


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


##
# TmuxClientXWindowIdMap
#

# TODO: Is it thread-safe?
class TmuxClientXWindowIdMap:

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


tmux_client_x_window_id_map = TmuxClientXWindowIdMap()


@app.route('/tmux/set_client_for_x_window_id', methods=['POST'])
def tmux_set_client_fox_x_window_id():
    data = flask.request.get_json()
    client = TmuxClient(hostname=data['hostname'],
                        client_name=data['client_name'])
    x_window_id = data['x_window_id']
    tmux_client_x_window_id_map[x_window_id] = client
    return ''


@app.route('/tmux/clear_client_for_x_window_id', methods=['POST'])
def tmux_clear_client_fox_x_window_id():
    data = flask.request.get_json()
    x_window_id = data['x_window_id']
    try:
        del tmux_client_x_window_id_map[x_window_id]
    except KeyError:
        pass
    return ''


##
# TmuxClientSessionMap
#

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


# TODO: Implement lock-forcing API:
# with tmux_client_session_map.lock() as locked_map:
#   for k in locked_map.keys(): ...
#   locked_map[...] = ...
# locked_map = tmux_client_session_map.lock


tmux_client_session_map = TmuxClientSessionMap()


def dump():
    print()
    pprint({
        k.client_name: v.session_name
        for k, v in tmux_client_session_map._map.items()
    })


@app.route('/tmux/client_session_changed', methods=['POST'])
def tmux_client_session_changed():
    data = flask.request.get_json()
    client = TmuxClient(hostname=data['hostname'],
                        client_name=data['client_name'])
    session = TmuxSession(hostname=data['hostname'],
                          server_pid=data['server_pid'],
                          session_name=data['session_name'])

    tmux_client_session_map[client] = session
    dump()
    return ''


@app.route('/tmux/client_detached', methods=['POST'])
def tmux_client_detached():
    data = flask.request.get_json()
    client = TmuxClient(hostname=data['hostname'],
                        client_name=data['client_name'])
    print('tmux_client_detached:', client)

    try:
        del tmux_client_session_map[client]
    except KeyError:
        pass
    dump()
    return ''


@app.route('/tmux/session_renamed', methods=['POST'])
def tmux_session_renamed():
    data = flask.request.get_json()
    client = TmuxClient(hostname=data['hostname'],
                        client_name=data['client_name'])
    new_session = TmuxSession(hostname=data['hostname'],
                              server_pid=data['server_pid'],
                              session_name=data['new_session_name'])

    tmux_client_session_map.session_renamed(client, new_session)
    dump()
    return ''


@app.route('/tmux/session_closed', methods=['POST'])
def tmux_session_closed():
    data = flask.request.get_json()
    session = TmuxSession(hostname=data['hostname'],
                          server_pid=data['server_pid'],
                          session_name=data['session_name'])
    print('tmux_session_closed:', session)

    tmux_client_session_map.session_closed(session)
    dump()
    return ''


def main():
    app.run(port=3141)  # TODO: run it a thread.


if __name__ == '__main__':
    main()
