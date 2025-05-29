# server.py

import grpc
from concurrent import futures
import time
import random

from logical_clock import LogicalClockWithHistory
import em_pb2
import em_pb2_grpc

def simulate_processing_delay(min_delay=0.5, max_delay=2.0):
    """Simulate server processing time."""
    delay = random.uniform(min_delay, max_delay)
    print(f"        [SERVER-PROCESSING] Processing delay: {delay:.2f}s")
    time.sleep(delay)

class ExclusionManagerServicer(em_pb2_grpc.ExclusionManagerServicer):
    def __init__(self, process_id, processing_delay_range=(0.5, 2.0)):
        self.clock = LogicalClockWithHistory(process_id)
        self.process_id = process_id
        self.processing_delay_range = processing_delay_range

    def RequestEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] ===== Incoming RequestEntry =====")
        print(f"[SERVER {self.process_id}] Received request from {request.process_id}")
        print(f"[SERVER {self.process_id}] Request timestamp: {request.timestamp}")
        print(f"[SERVER {self.process_id}] Resource: '{request.resource_id}'")
        
        # Show local time before processing
        local_time_before = self.clock.get_time()
        print(f"[SERVER {self.process_id}] Local time before processing: {local_time_before}")
        
        # FIXED: Update logical clock based on received message
        # This handles the "message received" event
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Local time after receiving message: {updated_time}")
        
        # Simulate server processing time
        min_delay, max_delay = self.processing_delay_range
        simulate_processing_delay(min_delay, max_delay)
        
        # Simulate some internal processing steps (local events)
        processing_steps = random.randint(1, 3)
        for step in range(processing_steps):
            step_time = self.clock.tick(f"internal processing step {step+1} for request from {request.process_id}")
            print(f"[SERVER {self.process_id}] Processing step {step+1} at time: {step_time}")
        
        # FIXED: Increment clock for sending reply (this is a separate local event)
        reply_timestamp = self.clock.tick(f"sending reply to {request.process_id}")
        
        print(f"[SERVER {self.process_id}] Sending reply with timestamp: {reply_timestamp}")
        print(f"[SERVER {self.process_id}] ===== End RequestEntry Processing =====")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message=f"Request granted by {self.process_id} at time {reply_timestamp}"
        )

    def ReplyEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] Received ReplyEntry from {request.process_id} "
              f"with timestamp {request.timestamp}")
        
        # FIXED: Update logical clock based on received message (single operation)
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Clock updated to: {updated_time}")
        
        # Simulate processing
        simulate_processing_delay(*self.processing_delay_range)
        
        # Increment clock for sending response
        reply_timestamp = self.clock.tick(f"sending response to ReplyEntry from {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Reply acknowledged"
        )

    def ReleaseEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] Received ReleaseEntry from {request.process_id} "
              f"with timestamp {request.timestamp} for resource '{request.resource_id}'")
        
        # FIXED: Update logical clock based on received message
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Clock updated to: {updated_time}")
        
        # Simulate processing
        simulate_processing_delay(*self.processing_delay_range)
        
        # Increment clock for sending acknowledgment
        reply_timestamp = self.clock.tick(f"sending release ack to {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Release acknowledged"
        )

    def GetStatus(self, request, context):
        print(f"[SERVER {self.process_id}] Status requested by {request.process_id}")
        
        # FIXED: Update clock for received message first
        updated_time = self.clock.update(0, sender_id=request.process_id)  # Status requests might not have timestamps
        
        # Then increment for sending response
        current_time = self.clock.tick(f"status query response to {request.process_id}")
        
        return em_pb2.StatusResponse(
            process_id=self.process_id,
            in_critical_section=False,
            current_timestamp=current_time,
            pending_requests=[]
        )

def serve(process_id, port, peers, processing_delay_range=(0.5, 2.0)):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ExclusionManagerServicer(process_id, processing_delay_range)
    em_pb2_grpc.add_ExclusionManagerServicer_to_server(servicer, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"[SERVER {process_id}] Started and listening on port {port}")
    print(f"[SERVER {process_id}] Processing delays: {processing_delay_range[0]}-{processing_delay_range[1]}s")
    print(f"[SERVER {process_id}] Will communicate with peers on ports: {peers}")
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\n[SERVER {process_id}] Shutting down...")
        # Print final clock history before shutdown
        servicer.clock.print_history()
        server.stop(0)