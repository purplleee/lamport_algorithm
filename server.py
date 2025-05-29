# server.py

import grpc
from concurrent import futures
import time

import em_pb2
import em_pb2_grpc

class ExclusionManagerServicer(em_pb2_grpc.ExclusionManagerServicer):
    def RequestEntry(self, request, context):
        print(f"[SERVER] Received RequestEntry from {request.process_id} at {request.timestamp}")
        return em_pb2.ReplyMessage(
            timestamp=request.timestamp,
            process_id="Server",
            granted=True,
            message="Request received"
        )

    def ReplyEntry(self, request, context):
        print(f"[SERVER] Received ReplyEntry from {request.process_id}")
        return em_pb2.ReplyMessage(
            timestamp=request.timestamp,
            process_id="Server",
            granted=True,
            message="Reply received"
        )

    def ReleaseEntry(self, request, context):
        print(f"[SERVER] Received ReleaseEntry from {request.process_id}")
        return em_pb2.ReplyMessage(
            timestamp=request.timestamp,
            process_id="Server",
            granted=True,
            message="Release acknowledged"
        )

    def GetStatus(self, request, context):
        print(f"[SERVER] Status requested by {request.process_id}")
        return em_pb2.StatusResponse(
            process_id=request.process_id,
            in_critical_section=False,
            current_timestamp=0,
            pending_requests=[]
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    em_pb2_grpc.add_ExclusionManagerServicer_to_server(ExclusionManagerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[SERVER] Listening on port 50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
