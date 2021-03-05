all: tmux_pb2.py tmux_pb2_grpc.py chrome_extension/chrome_pb.js chrome_extension/chrome_grpc_web_pb.js

tmux_pb2.py: tmux.proto
	python -m grpc_tools.protoc -I. --python_out=. tmux.proto

tmux_pb2_grpc.py: tmux.proto
	python -m grpc_tools.protoc -I. --grpc_python_out=. tmux.proto

test:
	python -m unittest discover -p '*test.py'

chrome_extension/chrome_pb.js: chrome.proto
	protoc -I=. chrome.proto --js_out=import_style=commonjs:chrome_extension --grpc-web_out=import_style=commonjs,mode=grpcweb:chrome_extension

chrome_extension/chrome_grpc_web_pb.js: chrome.proto
	protoc -I=. chrome.proto --js_out=import_style=commonjs:chrome_extension --grpc-web_out=import_style=commonjs,mode=grpcweb:chrome_extension
