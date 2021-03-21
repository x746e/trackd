import datetime
import unittest
from unittest import mock

import trackd
from trackd import SpanTracker
from tmux import TmuxClient, TmuxClientSessionMap, TmuxSession, TmuxAdapter


class TmuxClientSessionMapTest(unittest.TestCase):

    def test_session_renamed(self):
        session_map = TmuxClientSessionMap()
        client_foo = TmuxClient(client_name='foo', hostname='host')
        client_bar = TmuxClient(client_name='bar', hostname='host')
        old_session = TmuxSession(session_name='old', hostname='host', server_pid=42)
        new_session = TmuxSession(session_name='new', hostname='host', server_pid=42)
        # Set both clients to the same session.
        session_map[client_foo] = old_session
        session_map[client_bar] = old_session

        # Trigger session rename for one client.
        session_map.session_renamed(client=client_foo, new_session=new_session)

        # Check both clients now point to the new session.
        self.assertEqual(session_map[client_foo], new_session)
        self.assertEqual(session_map[client_bar], new_session)

    def test_session_closed(self):
        session_map = TmuxClientSessionMap()
        client_foo = TmuxClient(client_name='foo', hostname='host')
        client_bar = TmuxClient(client_name='bar', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        # Set both clients to the same session.
        session_map[client_foo] = session
        session_map[client_bar] = session

        # Signal session closure.
        session_map.session_closed(session)

        # Both clients shouldn't have an assigned session anymore.
        self.assertNotIn(client_foo, session_map)
        self.assertNotIn(client_bar, session_map)


class FakeSpanStorage:

    def __init__(self):
        self.spans = []

    def add(self, span):
        self.spans.append(span)


class TmuxAdapterTest(unittest.TestCase):

    def setUp(self):
        self.span_storage = FakeSpanStorage()
        self.span_tracker = SpanTracker(self.span_storage)
        self.adapter = TmuxAdapter(self.span_tracker)
        self.now_patcher = mock.patch.object(trackd, 'now')
        self.now = self.now_patcher.start()
        self.set_now(0)

    def tearDown(self):
        self.now_patcher.stop()

    def set_now(self, timestamp: int):
        self.now.return_value = datetime.datetime.fromtimestamp(timestamp)

    def test_session_closed(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, session)

        # Closing the session should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.session_closed(session)

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)

    def test_session_renamed(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        renamed_session = TmuxSession(session_name='renamed_session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, session)

        # Renaming the session should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.session_renamed(client, renamed_session)

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)

    def test_client_detached(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, session)

        # Detaching the client should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.client_detached(client)

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)

    def test_client_session_changed(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        first_session = TmuxSession(session_name='first_session', hostname='host', server_pid=42)
        second_session = TmuxSession(session_name='second_session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, first_session)

        # Changing the session should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.client_session_changed(client, second_session)

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, first_session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)

    def test_clear_client_for_x_window_id(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, session)

        # Removing tmux client ↔ X Window mapping should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.clear_client_for_x_window_id(x_window_id)

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)

    def test_set_focused_x_window_id(self):
        x_window_id = 42
        client = TmuxClient(client_name='client', hostname='host')
        session = TmuxSession(session_name='session', hostname='host', server_pid=42)
        # Activate a session in the adapter.
        self.set_now(0)
        self.adapter.set_focused_x_window_id(x_window_id, 'Terminal')
        self.adapter.set_client_for_x_window_id(x_window_id, client)
        self.adapter.client_session_changed(client, session)

        # X Window going out of focus should create a Span.
        duration = 120
        self.set_now(duration)
        self.adapter.set_focused_x_window_id(x_window_id - 1, 'Terminal')

        # Check the Span is there, and has the right name and duration.
        self.assertEqual(len(self.span_storage.spans), 1)
        (span,) = self.span_storage.spans
        self.assertEqual(span.session, session)
        self.assertEqual((span.end - span.start).total_seconds(), duration)


if __name__ == '__main__':
    unittest.main()
