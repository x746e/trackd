# It's hard to determine which gnome terminal this script is running in -- all
# of the windows are owned by the same process.  So, we are just remembering
# the currently focused one.

X_WINDOW_ID="$(xdotool getwindowfocus)"
# TODO: Check the window is indeed owned by gnome-terminal-server, to prevent
# races with random pop-ups.

function cleanup() {
    ./trackctl.sh tmux clear-client-for-x-window-id \
        --x_window_id "$X_WINDOW_ID"
}

trap cleanup EXIT

LC_TRACKD_X_WINDOW_ID="$X_WINDOW_ID" ssh -o SendEnv=LC_TRACKD_X_WINDOW_ID -R 3141:localhost:3141 $@
