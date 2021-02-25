from Xlib import X
from Xlib.display import Display
from Xlib.protocol.rq import Event


disp = Display()


NET_ACTIVE_WINDOW = disp.intern_atom('_NET_ACTIVE_WINDOW')


def handle_xevent(event: Event):
    """Handler for X events which ignores anything but focus/title change"""
    if event.type != X.PropertyNotify:
        return

    if event.atom != NET_ACTIVE_WINDOW:
        return

    window_id = event.window.get_full_property(
            NET_ACTIVE_WINDOW, X.AnyPropertyType).value[0]
    print(hex(window_id))


def main():
    root = disp.screen().root
    root.change_attributes(event_mask=X.PropertyChangeMask)

    while True:
        handle_xevent(disp.next_event())
