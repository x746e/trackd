#!/bin/sh

X_WINDOW_ID="$(xdotool getwindowfocus)"
# TODO: Check that window is indeed a terminal.
# Fail if it's not.  Allow ignoring with a flag.

./trackctl.sh tmux set-client-for-x-window-id \
    --hostname "$(hostname)" \
    --client_name "$(tty)" \
    --x_window_id "$X_WINDOW_ID"

function cleanup() {
    ./trackctl.sh tmux clear-client-for-x-window-id \
        --x_window_id "$X_WINDOW_ID"
}

trap cleanup EXIT

tmux $@

