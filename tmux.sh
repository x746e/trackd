#!/bin/sh

set -o errexit

if [[ -n "$LC_TRACKD_X_WINDOW_ID" ]]; then
  X_WINDOW_ID="$LC_TRACKD_X_WINDOW_ID"
else
  X_WINDOW_ID="$(xdotool getwindowfocus)"
fi

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

