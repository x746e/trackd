import click
import grpc

import tmux_pb2
import tmux_pb2_grpc


SERVER = 'localhost:3141'


@click.group()
def cli():
    pass


@cli.group()
def tmux():
    pass


@tmux.command()
@click.option('--hostname', required=True)
@click.option('--client_name', required=True)
@click.option('--x_window_id', type=int, required=True)
def set_client_for_x_window_id(hostname, client_name, x_window_id):
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.set_client_for_x_window_id(
                tmux_pb2.SetClientForXWindowIdRequest(
                    hostname=hostname,
                    client_name=client_name,
                    x_window_id=x_window_id,
                )
        )


@tmux.command()
@click.option('--x_window_id', type=int, required=True)
def clear_client_for_x_window_id(x_window_id):
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.clear_client_for_x_window_id(
                tmux_pb2.ClearClientForXWindowIdRequest(
                    x_window_id=x_window_id,
                )
        )


@tmux.command()
@click.option('--hostname', required=True)
@click.option('--client_name', required=True)
@click.option('--server_pid', type=int, required=True)
@click.option('--session_name', required=True)
def client_session_changed(hostname, client_name, server_pid, session_name):
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.client_session_changed(
                tmux_pb2.ClientSessionChangedRequest(
                    hostname=hostname,
                    client_name=client_name,
                    server_pid=server_pid,
                    session_name=session_name,
                )
        )


@tmux.command()
@click.option('--hostname', required=True)
@click.option('--client_name')
def client_detached(hostname, client_name):
    if not client_name:
        # If a client exists because a session is closed, client-detached hook
        # can't expand #{client_name} for some reason.
        return
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.client_detached(
                tmux_pb2.ClientDetachedRequest(
                    hostname=hostname,
                    client_name=client_name,
                )
        )


@tmux.command()
@click.option('--hostname', required=True)
@click.option('--client_name', required=True)
@click.option('--server_pid', type=int, required=True)
@click.option('--new_session_name', required=True)
def session_renamed(hostname, client_name, server_pid, new_session_name):
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.session_renamed(
                tmux_pb2.SessionRenamedRequest(
                    hostname=hostname,
                    client_name=client_name,
                    server_pid=server_pid,
                    new_session_name=new_session_name,
                )
        )


@tmux.command()
@click.option('--hostname', required=True)
@click.option('--server_pid', type=int, required=True)
@click.option('--session_name', required=True)
def session_closed(hostname, server_pid, session_name):
    with grpc.insecure_channel(SERVER) as channel:
        stub = tmux_pb2_grpc.TmuxStub(channel)
        response = stub.session_closed(
                tmux_pb2.SessionClosedRequest(
                    hostname=hostname,
                    server_pid=server_pid,
                    session_name=session_name,
                )
        )


if __name__ == '__main__':
    cli()
