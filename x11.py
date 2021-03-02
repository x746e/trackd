from typing import Callable, MutableSequence

from Xlib import X
from Xlib.display import Display
from Xlib.protocol.rq import Event


XWindowId = int
Callback = Callable[[XWindowId], None]


class XWindowFocusTracker:

    def __init__(self):
        self._callbacks: MutableSequence[Callback] = []
        self._disp = Display()
        self._current_window_id: Optional[XWindowId] = None
        self.NET_ACTIVE_WINDOW = self._disp.intern_atom('_NET_ACTIVE_WINDOW')

    def register(self, callback: Callback) -> None:
        self._callbacks.append(callback)

    def run(self) -> None:
        root = self._disp.screen().root
        root.change_attributes(event_mask=X.PropertyChangeMask)

        while True:
            self.handle_xevent(self._disp.next_event())

    def handle_xevent(self, event: Event) -> None:
        """Handler for X events which ignores anything but focus/title change"""
        if event.type != X.PropertyNotify:
            return

        if event.atom != self.NET_ACTIVE_WINDOW:
            return

        window_id = event.window.get_full_property(
                self.NET_ACTIVE_WINDOW, X.AnyPropertyType).value[0]

        if self._current_window_id == window_id:
            return
        self._current_window_id = window_id

        for callback in self._callbacks:
            callback(window_id)
