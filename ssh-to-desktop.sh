# It's hard to determine which gnome terminal this script is running in -- all
# of the windows are owned by the same process.  So, we are just remembering
# the currently focused one.
# TODO: Check the window is indeed owned by gnome-terminal-server, to prevent
# races with random pop-ups.
current_termninal_window="$(xdotool getwindowfocus)"
# communicate that to trackd
# ssh
