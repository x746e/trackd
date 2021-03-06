# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
import tmux_pb2 as tmux__pb2


class TmuxStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.set_client_for_x_window_id = channel.unary_unary(
                '/trackd.Tmux/set_client_for_x_window_id',
                request_serializer=tmux__pb2.SetClientForXWindowIdRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.clear_client_for_x_window_id = channel.unary_unary(
                '/trackd.Tmux/clear_client_for_x_window_id',
                request_serializer=tmux__pb2.ClearClientForXWindowIdRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.client_session_changed = channel.unary_unary(
                '/trackd.Tmux/client_session_changed',
                request_serializer=tmux__pb2.ClientSessionChangedRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.client_detached = channel.unary_unary(
                '/trackd.Tmux/client_detached',
                request_serializer=tmux__pb2.ClientDetachedRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.session_renamed = channel.unary_unary(
                '/trackd.Tmux/session_renamed',
                request_serializer=tmux__pb2.SessionRenamedRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )
        self.session_closed = channel.unary_unary(
                '/trackd.Tmux/session_closed',
                request_serializer=tmux__pb2.SessionClosedRequest.SerializeToString,
                response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString,
                )


class TmuxServicer(object):
    """Missing associated documentation comment in .proto file."""

    def set_client_for_x_window_id(self, request, context):
        """Methods for maintaining X Window ID ??? tmux client mapping.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def clear_client_for_x_window_id(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def client_session_changed(self, request, context):
        """Methods for maintaining tmux client ??? session mapping.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def client_detached(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def session_renamed(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def session_closed(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TmuxServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'set_client_for_x_window_id': grpc.unary_unary_rpc_method_handler(
                    servicer.set_client_for_x_window_id,
                    request_deserializer=tmux__pb2.SetClientForXWindowIdRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'clear_client_for_x_window_id': grpc.unary_unary_rpc_method_handler(
                    servicer.clear_client_for_x_window_id,
                    request_deserializer=tmux__pb2.ClearClientForXWindowIdRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'client_session_changed': grpc.unary_unary_rpc_method_handler(
                    servicer.client_session_changed,
                    request_deserializer=tmux__pb2.ClientSessionChangedRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'client_detached': grpc.unary_unary_rpc_method_handler(
                    servicer.client_detached,
                    request_deserializer=tmux__pb2.ClientDetachedRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'session_renamed': grpc.unary_unary_rpc_method_handler(
                    servicer.session_renamed,
                    request_deserializer=tmux__pb2.SessionRenamedRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
            'session_closed': grpc.unary_unary_rpc_method_handler(
                    servicer.session_closed,
                    request_deserializer=tmux__pb2.SessionClosedRequest.FromString,
                    response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'trackd.Tmux', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Tmux(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def set_client_for_x_window_id(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/set_client_for_x_window_id',
            tmux__pb2.SetClientForXWindowIdRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def clear_client_for_x_window_id(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/clear_client_for_x_window_id',
            tmux__pb2.ClearClientForXWindowIdRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def client_session_changed(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/client_session_changed',
            tmux__pb2.ClientSessionChangedRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def client_detached(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/client_detached',
            tmux__pb2.ClientDetachedRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def session_renamed(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/session_renamed',
            tmux__pb2.SessionRenamedRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def session_closed(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/trackd.Tmux/session_closed',
            tmux__pb2.SessionClosedRequest.SerializeToString,
            google_dot_protobuf_dot_empty__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
