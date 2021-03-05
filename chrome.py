import sys
from wsgiref.simple_server import make_server
import sonora.wsgi

from google.protobuf import empty_pb2

import chrome_pb2_grpc


class Chrome(chrome_pb2_grpc.ChromeServicer):

    def __init__(self, span_tracker):
        self._span_tracker = span_tracker

    def session_changed(self, request, context):
        print(request)
        return empty_pb2.Empty()


def serve(servicer):
    grpc_wsgi_app = sonora.wsgi.grpcWSGI(None)

    with make_server("", 3142, grpc_wsgi_app) as httpd:
        chrome_pb2_grpc.add_ChromeServicer_to_server(servicer, grpc_wsgi_app)
        httpd.serve_forever()
