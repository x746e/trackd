all: tmux_pb2.py tmux_pb2_grpc.py

tmux_pb2.py: tmux.proto
	python -m grpc_tools.protoc -I. --python_out=. tmux.proto

tmux_pb2_grpc.py: tmux.proto
	python -m grpc_tools.protoc -I. --grpc_python_out=. tmux.proto

test:
	python -m unittest discover -p '*test.py'

