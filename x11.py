import logging
import subprocess
import threading

from typing import Callable, MutableSequence

import Xlib.error
from Xlib import X
from Xlib.display import Display
from Xlib.protocol.rq import Event


XWindowId = int
Callback = Callable[[XWindowId, str], None]


class XWindowFocusTracker:

    def __init__(self):
        self._callbacks: MutableSequence[Callback] = []
        self._disp = Display()
        self._current_window_id: Optional[XWindowId] = None
        self.NET_ACTIVE_WINDOW = self._disp.intern_atom('_NET_ACTIVE_WINDOW')
        self.NET_WM_NAME = self._disp.intern_atom('_NET_WM_NAME')
        self._screen_locked = False
        self._lock = threading.Lock()

    def register(self, callback: Callback) -> None:
        with self._lock:
            self._callbacks.append(callback)

    def run(self) -> None:
        screen_lock_tracker = ScreenLockTracker(self)
        screen_lock_tracker_thread = threading.Thread(target=screen_lock_tracker.run, daemon=True)
        screen_lock_tracker_thread.start()

        root = self._disp.screen().root
        root.change_attributes(event_mask=X.PropertyChangeMask)

        while True:
            self._handle_xevent(self._disp.next_event())

    def set_screen_locked(self, locked: bool) -> None:
        logging.info(f'XWindowFocusTracker.set_screen_locked(locked={locked})')
        with self._lock:
            self._screen_locked = locked
            if locked:
                window_id = -1
                window_name = 'locked'
            else:
                window_id = self._current_window_id
                window_name = self._get_window_name(window_id)
            for callback in self._callbacks:
                callback(window_id, window_name)


    def _handle_xevent(self, event: Event) -> None:
        """Handler for X events which ignores anything but focus/title change"""
        if event.type != X.PropertyNotify:
            return

        if event.atom != self.NET_ACTIVE_WINDOW:
            return

        window_id = event.window.get_full_property(
                self.NET_ACTIVE_WINDOW, X.AnyPropertyType).value[0]

        with self._lock:
            if self._current_window_id == window_id:
                return
            self._current_window_id = window_id

            window_name = self._get_window_name(window_id)

            for callback in self._callbacks:
                callback(window_id, window_name)

    def _get_window_name(self, window_id: XWindowId) -> str:
        window_obj = self._disp.create_resource_object('window', window_id)
        try:
            window_name_property = window_obj.get_full_property(self.NET_WM_NAME, 0)
        except Xlib.error.BadWindow:
            return ''
        else:
            return window_name_property.value.decode('utf-8')


class ScreenLockTracker:

    def __init__(self, tracker):
        self._tracker = tracker

    def run(self) -> None:
        self._proc = subprocess.Popen('gdbus monitor -y -d org.freedesktop.login1'.split(),
                                      stdout=subprocess.PIPE)
        assert self._proc.stdout is not None  # ..to make typecheckers happy.
        for line in self._proc.stdout:
            if b"{'LockedHint': <true>}" in line:
                self._tracker.set_screen_locked(True)
            elif b"{'LockedHint': <false>}" in line:
                self._tracker.set_screen_locked(False)
