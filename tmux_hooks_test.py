import os
import pathlib
import subprocess
import tempfile
import time
import unittest

import ptyprocess

from typing import Sequence


def get_tty(pid: int) -> str:
    """Returns tty (e.g. "pts/11") for a PID."""
    return subprocess.check_output(f'ps -p {pid} -o tty --no-headers'.split()).strip().decode('utf-8')


class TmuxHooksTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = pathlib.Path(self.temp_dir_obj.name)
        self.server_socket = self.temp_dir / 'tmux-server.socket'
        self.config_file = self.temp_dir / 'tmux.conf'
        self.log_file = self.temp_dir / 'log'
        self.tmux = 'tmux'
        # self.tmux = '/home/ksp/src/tmux/tmux'
        self.maxDiff = 2000

    def tearDown(self):
        if self.server_socket.exists():
            subprocess.check_call(f'{self.tmux} -f /dev/null -S {self.server_socket} kill-server'.split())
        self.temp_dir_obj.cleanup()

    def _get_hook_log(self, hook_name: str) -> str:
        variables = ['client_name', 'client_session', 'hook_session_name', 'session_name']
        log_record = r'++++ #{hook}\\n  ' + '  '.join([r'%(var)s: #{%(var)s}\\n' % {'var': var} for var in variables])
        hook_log = """
set-hook -g %(hook)s "run-shell 'echo -e ''%(log_record)s'' >> %(log_file)s'"
""" % {'hook': hook_name, 'log_record': log_record, 'log_file': self.log_file}
        return hook_log.replace(r'\\', r'\\\\').strip()

    def _get_config(self, hook_names: Sequence[str]) -> str:
        config = ['set -g assume-paste-time 0']
        config += [self._get_hook_log(hook_name) for hook_name in hook_names]
        return '\n'.join(config)

    def setup_config(self, hook_names):
        with open(self.config_file, 'wt') as f:
            f.write(self._get_config(hook_names=hook_names))

    def test_creating_new_session_emits_client_session_changed(self):
        self.setup_config(hook_names=['client-session-changed'])

        # Create the first tmux session.  That will also start a tmux server.
        first = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} new -s alpha'.split())
        first.read()
        time.sleep(.1)

        self.assertLogs(f"""
++++ client-session-changed
 client_name: /dev/{get_tty(first.pid)}
 client_session: alpha
 hook_session_name: 
 session_name: alpha
""")

    def test_creating_new_session_form_inside_tmux_emits_client_session_changed(self):
        self.setup_config(hook_names=['client-session-changed'])

        # Create the first tmux session.  That will also start a tmux server.
        first = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} new -s alpha'.split())
        first.read()
        time.sleep(.1)

        # Create another session from inside tmux.
        first.sendcontrol(b'b')
        first.write(b':')
        time.sleep(.1)
        first.write(b'new-session -s beta\n')
        time.sleep(.1)
        first.read()

        self.assertLogs(f"""
++++ client-session-changed
 client_name: /dev/{get_tty(first.pid)}
 client_session: alpha
 hook_session_name: 
 session_name: alpha

++++ client-session-changed
 client_name: /dev/{get_tty(first.pid)}
 client_session: beta
 hook_session_name: 
 session_name: beta
""")

    def test_session_renamed(self):
        self.setup_config(hook_names=['client-session-changed', 'session-renamed'])

        # Create the first tmux session.  That will also start a tmux server.
        first = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} new -s alpha'.split())
        first.read()
        time.sleep(.1)

        # Rename the session.
        first.sendcontrol(b'b')
        first.write(b':')
        time.sleep(.1)
        first.write(b'rename-session alpha-renamed\n')
        time.sleep(.1)
        first.read()
        time.sleep(.1)

        self.assertLogs(f"""
++++ client-session-changed
 client_name: /dev/{get_tty(first.pid)}
 client_session: alpha
 hook_session_name: 
 session_name: alpha

++++ session-renamed
 client_name: /dev/{get_tty(first.pid)}
 client_session: alpha-renamed
 hook_session_name: alpha-renamed
 session_name: alpha-renamed
""")

    def test_session_closed(self):
        self.setup_config(hook_names=['client-session-changed', 'session-closed'])

        # Create the first tmux session.  That will also start a tmux server.
        first = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} new -s alpha'.split())
        first.read()
        time.sleep(.1)
        first_tty = get_tty(first.pid)

        # Detach the first tmux session.
        first.sendcontrol(b'b')
        first.write(b'd')
        time.sleep(.1)
        first.read()

        # Create the second tmux session.
        second = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} new -s beta'.split())
        second.read()
        time.sleep(.1)
        second_tty = get_tty(second.pid)

        # Connect to the second session with another client.
        third = ptyprocess.PtyProcess.spawn(f'{self.tmux} -f {self.config_file} -S {self.server_socket} atta -t beta'.split())
        third.read()
        time.sleep(.1)
        third_tty = get_tty(third.pid)

        # Try exiting the second session, see what kind of hooks are called.
        third.write(b'exit\n')
        time.sleep(.1)
        third.read()
        time.sleep(.1)

        self.assertLogs(f"""
++++ client-session-changed
 client_name: /dev/{first_tty}
 client_session: alpha
 hook_session_name: 
 session_name: alpha

++++ client-session-changed
 client_name: /dev/{second_tty}
 client_session: beta
 hook_session_name: 
 session_name: beta

++++ client-session-changed
 client_name: /dev/{third_tty}
 client_session: beta
 hook_session_name: 
 session_name: beta

++++ session-closed
 client_name: 
 client_session: 
 hook_session_name: beta
 session_name: alpha
""")

    def assertLogs(self, expected):
        with open(self.log_file, 'rt') as f:
            actual = f.read()
        self.assertEqual(expected.strip(), actual.strip())


if __name__ == '__main__':
    unittest.main()
