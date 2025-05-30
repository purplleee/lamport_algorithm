# server.py - Enhanced with Mutual Exclusion Logic

import grpc
from concurrent import futures
import time
import random
import threading
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional

from logical_clock import LogicalClockWithHistory
import em_pb2
import em_pb2_grpc

@dataclass
class Request:
    timestamp: int
    process_id: str
    resource_id: str
    
    def __lt__(self, other):
        # For priority queue ordering: earlier timestamp first
        # If timestamps are equal, use process_id for tie-breaking
        if self.timestamp == other.timestamp:
            return self.process_id < other.process_id
        return self.timestamp < other.timestamp

class MutualExclusionState:
    def __init__(self, process_id: str, peer_ports: List[int]):
        self.process_id = process_id
        self.peer_ports = peer_ports
        self.lock = threading.RLock()
        
        # Request queue (priority queue based on timestamp)
        self.request_queue = []
        
        # Track replies received for our own requests
        self.pending_replies: Dict[str, set] = {}  # resource_id -> set of process_ids we're waiting for
        
        # Track if we're in critical section
        self.in_critical_section = False
        self.current_resource = None
        
        # Track our own requests
        self.our_requests: Dict[str, Request] = {}  # resource_id -> our request
        
    def add_request(self, request: Request):
        """Add a request to the priority queue."""
        with self.lock:
            # Remove any existing request from the same process for the same resource
            self.request_queue = [r for r in self.request_queue 
                                if not (r.process_id == request.process_id and r.resource_id == request.resource_id)]
            
            # Add new request and sort
            self.request_queue.append(request)
            self.request_queue.sort()
            
            print(f"[MUTEX] Added request to queue: {request}")
            self._print_queue_state()
    
    def remove_request(self, process_id: str, resource_id: str):
        """Remove a request from the queue."""
        with self.lock:
            original_len = len(self.request_queue)
            self.request_queue = [r for r in self.request_queue 
                                if not (r.process_id == process_id and r.resource_id == resource_id)]
            
            if len(self.request_queue) < original_len:
                print(f"[MUTEX] Removed request from {process_id} for resource {resource_id}")
                self._print_queue_state()
    
    def can_enter_critical_section(self, resource_id: str) -> bool:
        """Check if we can enter critical section for the given resource."""
        with self.lock:
            if self.in_critical_section:
                return False
                
            # Check if we have a request for this resource
            if resource_id not in self.our_requests:
                return False
            
            our_request = self.our_requests[resource_id]
            
            # Check if our request is at the front of the queue
            if not self.request_queue or self.request_queue[0] != our_request:
                return False
            
            # Check if we've received replies from all other processes
            if resource_id in self.pending_replies:
                expected_replies = {f"Process-{i+1}" for i in range(len(self.peer_ports) + 1) 
                                  if f"Process-{i+1}" != self.process_id}
                received_replies = self.pending_replies[resource_id]
                
                if not expected_replies.issubset(received_replies):
                    missing = expected_replies - received_replies
                    print(f"[MUTEX] Still waiting for replies from: {missing}")
                    return False
            
            return True
    
    def enter_critical_section(self, resource_id: str):
        """Enter critical section."""
        with self.lock:
            self.in_critical_section = True
            self.current_resource = resource_id
            print(f"[MUTEX] *** ENTERED CRITICAL SECTION for resource {resource_id} ***")
    
    def exit_critical_section(self):
        """Exit critical section."""
        with self.lock:
            resource_id = self.current_resource
            self.in_critical_section = False
            self.current_resource = None
            
            # Remove our request from queue
            if resource_id in self.our_requests:
                self.remove_request(self.process_id, resource_id)
                del self.our_requests[resource_id]
            
            # Clear pending replies for this resource
            if resource_id in self.pending_replies:
                del self.pending_replies[resource_id]
            
            print(f"[MUTEX] *** EXITED CRITICAL SECTION for resource {resource_id} ***")
            self._print_queue_state()
    
    def add_reply(self, resource_id: str, from_process: str):
        """Record a reply received for our request."""
        with self.lock:
            if resource_id not in self.pending_replies:
                self.pending_replies[resource_id] = set()
            
            self.pending_replies[resource_id].add(from_process)
            print(f"[MUTEX] Received reply from {from_process} for resource {resource_id}")
            print(f"[MUTEX] Replies so far: {self.pending_replies[resource_id]}")
    
    def add_our_request(self, request: Request):
        """Add our own request."""
        with self.lock:
            self.our_requests[request.resource_id] = request
            self.add_request(request)
            
            # Initialize pending replies tracking
            self.pending_replies[request.resource_id] = set()
    
    def _print_queue_state(self):
        """Print current state of the request queue."""
        print(f"[MUTEX] Current queue state:")
        for i, req in enumerate(self.request_queue):
            marker = " <- OURS" if req.process_id == self.process_id else ""
            print(f"[MUTEX]   {i+1}. T={req.timestamp}, P={req.process_id}, R={req.resource_id}{marker}")
        if not self.request_queue:
            print(f"[MUTEX]   (empty)")

def simulate_processing_delay(min_delay=0.5, max_delay=2.0):
    """Simulate server processing time."""
    delay = random.uniform(min_delay, max_delay)
    print(f"        [SERVER-PROCESSING] Processing delay: {delay:.2f}s")
    time.sleep(delay)

def simulate_critical_section_work(duration_range=(2, 5)):
    """Simulate work in critical section."""
    duration = random.uniform(*duration_range)
    print(f"        [CRITICAL-SECTION] Working for {duration:.2f}s...")
    time.sleep(duration)

class ExclusionManagerServicer(em_pb2_grpc.ExclusionManagerServicer):
    def __init__(self, process_id, peer_ports, processing_delay_range=(0.5, 2.0)):
        self.clock = LogicalClockWithHistory(process_id)
        self.process_id = process_id
        self.peer_ports = peer_ports
        self.processing_delay_range = processing_delay_range
        self.mutex_state = MutualExclusionState(process_id, peer_ports)

    def RequestEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] ===== Incoming RequestEntry =====")
        print(f"[SERVER {self.process_id}] Received request from {request.process_id}")
        print(f"[SERVER {self.process_id}] Request timestamp: {request.timestamp}")
        print(f"[SERVER {self.process_id}] Resource: '{request.resource_id}'")
        
        # Update logical clock for received message
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Clock updated to: {updated_time}")
        
        # Add request to our queue
        incoming_request = Request(
            timestamp=request.timestamp,
            process_id=request.process_id,
            resource_id=request.resource_id
        )
        self.mutex_state.add_request(incoming_request)
        
        # Simulate processing delay
        simulate_processing_delay(*self.processing_delay_range)
        
        # Send reply (increment clock for sending reply)
        reply_timestamp = self.clock.tick(f"sending reply to {request.process_id}")
        
        print(f"[SERVER {self.process_id}] Sending reply with timestamp: {reply_timestamp}")
        print(f"[SERVER {self.process_id}] ===== End RequestEntry Processing =====")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message=f"Request acknowledged by {self.process_id}"
        )

    def ReplyEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] Received ReplyEntry from {request.process_id}")
        
        # Update logical clock
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Clock updated to: {updated_time}")
        
        # This method would be used in some mutual exclusion algorithms
        # For Lamport's algorithm, replies are handled differently
        
        reply_timestamp = self.clock.tick(f"acknowledging ReplyEntry from {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Reply acknowledged"
        )

    def ReleaseEntry(self, request, context):
        print(f"\n[SERVER {self.process_id}] ===== Incoming ReleaseEntry =====")
        print(f"[SERVER {self.process_id}] Received release from {request.process_id}")
        print(f"[SERVER {self.process_id}] Release timestamp: {request.timestamp}")
        print(f"[SERVER {self.process_id}] Resource: '{request.resource_id}'")
        
        # Update logical clock
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        print(f"[SERVER {self.process_id}] Clock updated to: {updated_time}")
        
        # Remove the released request from our queue
        self.mutex_state.remove_request(request.process_id, request.resource_id)
        
        # Check if we can now enter critical section
        self._check_and_enter_critical_section()
        
        # Simulate processing
        simulate_processing_delay(*self.processing_delay_range)
        
        reply_timestamp = self.clock.tick(f"acknowledging release from {request.process_id}")
        
        print(f"[SERVER {self.process_id}] ===== End ReleaseEntry Processing =====")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Release acknowledged"
        )

    def GetStatus(self, request, context):
        current_time = self.clock.tick(f"status query from {request.process_id}")
        
        with self.mutex_state.lock:
            pending = [f"{r.process_id}:{r.resource_id}:T{r.timestamp}" 
                      for r in self.mutex_state.request_queue]
        
        return em_pb2.StatusResponse(
            process_id=self.process_id,
            in_critical_section=self.mutex_state.in_critical_section,
            current_timestamp=current_time,
            pending_requests=pending
        )
    
    def request_critical_section(self, resource_id: str):
        """Request access to critical section (called by client thread)."""
        print(f"\n[MUTEX {self.process_id}] ===== Requesting Critical Section =====")
        
        # Create our request
        request_timestamp = self.clock.tick(f"requesting access to {resource_id}")
        our_request = Request(
            timestamp=request_timestamp,
            process_id=self.process_id,
            resource_id=resource_id
        )
        
        # Add to our state
        self.mutex_state.add_our_request(our_request)
        
        # Send request to all other processes
        self._broadcast_request(our_request)
        
        # Wait until we can enter critical section
        self._wait_for_critical_section_access(resource_id)
        
        # Enter critical section
        self.mutex_state.enter_critical_section(resource_id)
        
        # Simulate work in critical section
        simulate_critical_section_work()
        
        # Exit and release
        self.mutex_state.exit_critical_section()
        self._broadcast_release(resource_id)
        
        print(f"[MUTEX {self.process_id}] ===== Critical Section Complete =====")
    
    def _broadcast_request(self, request: Request):
        """Send request to all peer processes."""
        print(f"[MUTEX {self.process_id}] Broadcasting request to all peers...")
        
        for peer_port in self.peer_ports:
            try:
                channel = grpc.insecure_channel(f'localhost:{peer_port}')
                stub = em_pb2_grpc.ExclusionManagerStub(channel)
                
                # Send request and handle reply
                reply = stub.RequestEntry(em_pb2.RequestMessage(
                    timestamp=request.timestamp,
                    process_id=request.process_id,
                    resource_id=request.resource_id
                ))
                
                # Update clock based on reply
                updated_time = self.clock.update(reply.timestamp, sender_id=reply.process_id)
                print(f"[MUTEX {self.process_id}] Received reply from port {peer_port}, clock: {updated_time}")
                
                # Record the reply
                self.mutex_state.add_reply(request.resource_id, reply.process_id)
                
                channel.close()
                
            except Exception as e:
                print(f"[MUTEX {self.process_id}] Failed to send request to port {peer_port}: {e}")
    
    def _wait_for_critical_section_access(self, resource_id: str):
        """Wait until we can access the critical section."""
        print(f"[MUTEX {self.process_id}] Waiting for critical section access...")
        
        while not self.mutex_state.can_enter_critical_section(resource_id):
            time.sleep(0.1)  # Small delay to avoid busy waiting
        
        print(f"[MUTEX {self.process_id}] Conditions met for critical section entry!")
    
    def _check_and_enter_critical_section(self):
        """Check if we can enter critical section for any of our pending requests."""
        with self.mutex_state.lock:
            for resource_id in list(self.mutex_state.our_requests.keys()):
                if self.mutex_state.can_enter_critical_section(resource_id):
                    print(f"[MUTEX {self.process_id}] Can now enter critical section for {resource_id}!")
                    # Note: In a real implementation, you might want to signal a waiting thread
                    # For this demo, we'll let the waiting loop in _wait_for_critical_section_access handle it
    
    def _broadcast_release(self, resource_id: str):
        """Send release message to all peer processes."""
        print(f"[MUTEX {self.process_id}] Broadcasting release to all peers...")
        
        release_timestamp = self.clock.tick(f"releasing {resource_id}")
        
        for peer_port in self.peer_ports:
            try:
                channel = grpc.insecure_channel(f'localhost:{peer_port}')
                stub = em_pb2_grpc.ExclusionManagerStub(channel)
                
                reply = stub.ReleaseEntry(em_pb2.ReleaseMessage(
                    timestamp=release_timestamp,
                    process_id=self.process_id,
                    resource_id=resource_id
                ))
                
                # Update clock based on reply
                updated_time = self.clock.update(reply.timestamp, sender_id=reply.process_id)
                print(f"[MUTEX {self.process_id}] Release acknowledged by port {peer_port}, clock: {updated_time}")
                
                channel.close()
                
            except Exception as e:
                print(f"[MUTEX {self.process_id}] Failed to send release to port {peer_port}: {e}")

def serve(process_id, port, peers, processing_delay_range=(0.5, 2.0)):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ExclusionManagerServicer(process_id, peers, processing_delay_range)
    em_pb2_grpc.add_ExclusionManagerServicer_to_server(servicer, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"[SERVER {process_id}] Started with mutual exclusion support on port {port}")
    print(f"[SERVER {process_id}] Processing delays: {processing_delay_range[0]}-{processing_delay_range[1]}s")
    print(f"[SERVER {process_id}] Peers: {peers}")
    
    # Store servicer globally so client can access it
    global _servicer
    _servicer = servicer
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\n[SERVER {process_id}] Shutting down...")
        servicer.clock.print_history()
        server.stop(0)

# Global variable to allow client access to servicer
_servicer = None

def get_servicer():
    """Get the current servicer instance (for client use)."""
    return _servicer