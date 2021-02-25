import pathlib
import subprocess
import tempfile
import time

import ptyprocess

temp_dir_obj = tempfile.TemporaryDirectory()
temp_dir = pathlib.Path(temp_dir_obj.name)
print(f'temp_dir: {temp_dir}')
server_socket = temp_dir / 'tmux-server.socket'
config_file = temp_dir / 'tmux.conf'
log_file = temp_dir / 'log'

with open(config_file, 'wt') as f:
    f.write(r"""
set -g assume-paste-time 0
set-hook -g client-attached "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
set-hook -g client-detached "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
set-hook -g client-session-changed "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
set-hook -g session-created "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
set-hook -g session-closed "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
set-hook -g session-renamed "run-shell 'echo -e ''++++ #{hook}\\\\n  client_name: #{client_name}\\\\n  client_session: #{client_session}\\\\n  hook_session_name: #{hook_session_name}\\\\n  session_name: #{session_name}\\\\n'' >> %(log_file)s'"
    """ % {'log_file': log_file})


tmux = 'tmux'
# tmux = '/home/ksp/src/tmux/tmux'


# Create the first tmux session.  That will also start a tmux server.
first = ptyprocess.PtyProcess.spawn(f'{tmux} -f {config_file} -S {server_socket} new -s alpha'.split())
first.read()
time.sleep(.1)

first.sendcontrol(b'b')
first.write(b'd')
time.sleep(.1)
first.read()

# Create the second tmux session.
second = ptyprocess.PtyProcess.spawn(f'{tmux} -f {config_file} -S {server_socket} new -s beta'.split())
second.read()
time.sleep(.1)

# Connect to the second session with another client.
third = ptyprocess.PtyProcess.spawn(f'{tmux} -f {config_file} -S {server_socket} atta -t beta'.split())
third.read()
time.sleep(.1)

# Try exiting the second session, see what kind of hooks are called.
third.write(b'exit\n')
time.sleep(.1)
third.read()
time.sleep(.1)

print(open(log_file, 'rt').read())

subprocess.check_call(f'{tmux} -f /dev/null -S {server_socket} kill-server'.split())


# Things trackd relies on:
# * when session is closed, there's a session-closed hook called with #{hook_session_name} set.
