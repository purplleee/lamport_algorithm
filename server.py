# server.py

import grpc
from concurrent import futures
import time

from logical_clock import LogicalClockWithHistory
import em_pb2
import em_pb2_grpc

class ExclusionManagerServicer(em_pb2_grpc.ExclusionManagerServicer):
    def __init__(self, process_id):
        self.clock = LogicalClockWithHistory(process_id)
        self.process_id = process_id

    def RequestEntry(self, request, context):
        # Update logical clock based on received message
        self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Received RequestEntry from {request.process_id} "
              f"with timestamp {request.timestamp} for resource '{request.resource_id}'")
        
        # Increment clock for sending reply
        reply_timestamp = self.clock.tick(f"sending reply to {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message=f"Request granted by {self.process_id}"
        )

    def ReplyEntry(self, request, context):
        # Update logical clock based on received message
        self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Received ReplyEntry from {request.process_id} "
              f"with timestamp {request.timestamp}")
        
        # Increment clock for sending response
        reply_timestamp = self.clock.tick(f"sending response to ReplyEntry from {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Reply acknowledged"
        )

    def ReleaseEntry(self, request, context):
        # Update logical clock based on received message
        self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Received ReleaseEntry from {request.process_id} "
              f"with timestamp {request.timestamp} for resource '{request.resource_id}'")
        
        # Increment clock for sending acknowledgment
        reply_timestamp = self.clock.tick(f"sending release ack to {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Release acknowledged"
        )

    def GetStatus(self, request, context):
        # This is a query operation, increment clock
        current_time = self.clock.tick(f"status query from {request.process_id}")
        print(f"[SERVER {self.process_id}] Status requested by {request.process_id}")
        
        return em_pb2.StatusResponse(
            process_id=self.process_id,
            in_critical_section=False,
            current_timestamp=current_time,
            pending_requests=[]
        )

def serve(process_id, port, peers):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ExclusionManagerServicer(process_id)
    em_pb2_grpc.add_ExclusionManagerServicer_to_server(servicer, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"[SERVER {process_id}] Started and listening on port {port}")
    print(f"[SERVER {process_id}] Will communicate with peers on ports: {peers}")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"[SERVER {process_id}] Shutting down...")
        # Print final clock history before shutdown
        servicer.clock.print_history()
        server.stop(0)