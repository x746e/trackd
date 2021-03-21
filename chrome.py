from dataclasses import dataclass
import logging
import sys
import threading

from typing import Optional

import cherrypy

import x11


@dataclass(frozen=True)
class ChromeSession:
    """Chrome sessions are represented by the chrome user + session name."""
    session_name: str
    user: str


class ChromeAdapter:

    def __init__(self, span_tracker):
        self._lock = threading.Lock()
        self._span_tracker = span_tracker
        self._current_session: Optional[ChromeSession] = None
        self._chrome_is_focused = False

    def _check_span(self):
        if self._current_session is None:
            self._span_tracker.update_active_session(None)
            return
        if not self._chrome_is_focused:
            self._span_tracker.update_active_session(None)
            return

        self._span_tracker.update_active_session(self._current_session)

    def session_changed(self, session: ChromeSession) -> None:
        logging.debug(f'ChromeAdapter.session_changed({session!r})')
        with self._lock:
            if (session.session_name is None and
                    self._current_session is not None and
                    session.user == self._current_session.user):
                self._current_session = None
                return
            self._current_session = session
            self._check_span()

    def set_focused_x_window_id(self, x_window_id: x11.XWindowId, window_name: str) -> None:
        with self._lock:
            self._chrome_is_focused = 'Google Chrome' in window_name
            self._check_span()


class Chrome():
    """Webserver for getting updates from Chrome."""

    def __init__(self, chrome_adapter: ChromeAdapter):
        self._chrome_adapter = chrome_adapter

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def session_changed(self):
        if cherrypy.request.method != 'POST':
            return

        session = ChromeSession(**cherrypy.request.json)
        self._chrome_adapter.session_changed(session)

        return {}


def serve(chrome_http: Chrome, port: int):
    cherrypy.config.update({
        'global': {'engine.autoreload.on' : False},
    })
    cherrypy.config.update({
	'server.socket_port': port,
	'tools.response_headers.on': True,
	'tools.response_headers.headers': [
            ('Access-Control-Allow-Origin', '*'),
            ('Access-Control-Allow-Methods', 'OPTIONS,POST'),
            ('Access-Control-Allow-Headers', 'Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers'),
        ],
        'log.screen': False,
    })
    cherrypy.quickstart(chrome_http)
