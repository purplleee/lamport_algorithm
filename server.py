# server.py - Clean Enhanced Mutual Exclusion Implementation

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
        self.pending_replies: Dict[str, set] = {}
        
        # Track if we're in critical section
        self.in_critical_section = False
        self.current_resource = None
        
        # Track our own requests
        self.our_requests: Dict[str, Request] = {}
        
    def add_request(self, request: Request):
        """Add a request to the priority queue."""
        with self.lock:
            # Remove any existing request from the same process for the same resource
            self.request_queue = [r for r in self.request_queue 
                                if not (r.process_id == request.process_id and r.resource_id == request.resource_id)]
            
            # Add new request and sort
            self.request_queue.append(request)
            self.request_queue.sort()
            
            print(f"🔒 [{self.process_id}] Queue: {request.process_id} added (T={request.timestamp}, R={request.resource_id})")
            self._print_queue_status()
    
    def remove_request(self, process_id: str, resource_id: str):
        """Remove a request from the queue."""
        with self.lock:
            original_len = len(self.request_queue)
            self.request_queue = [r for r in self.request_queue 
                                if not (r.process_id == process_id and r.resource_id == resource_id)]
            
            if len(self.request_queue) < original_len:
                print(f"🔓 [{self.process_id}] Queue: {process_id} removed from {resource_id}")
                self._print_queue_status()
    
    def can_enter_critical_section(self, resource_id: str) -> bool:
        """Check if we can enter critical section for the given resource."""
        with self.lock:
            if self.in_critical_section:
                return False
                
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
                    return False
            
            return True
    
    def enter_critical_section(self, resource_id: str):
        """Enter critical section."""
        with self.lock:
            self.in_critical_section = True
            self.current_resource = resource_id
            print(f"🎯 [{self.process_id}] *** ENTERED CRITICAL SECTION: {resource_id} ***")
    
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
            
            print(f"✅ [{self.process_id}] *** EXITED CRITICAL SECTION: {resource_id} ***")
    
    def add_reply(self, resource_id: str, from_process: str):
        """Record a reply received for our request."""
        with self.lock:
            if resource_id not in self.pending_replies:
                self.pending_replies[resource_id] = set()
            
            self.pending_replies[resource_id].add(from_process)
            print(f"💬 [{self.process_id}] Reply from {from_process} for {resource_id} ({len(self.pending_replies[resource_id])} total)")
    
    def add_our_request(self, request: Request):
        """Add our own request."""
        with self.lock:
            self.our_requests[request.resource_id] = request
            self.add_request(request)
            self.pending_replies[request.resource_id] = set()
    
    def _print_queue_status(self):
        """Print current state of the request queue."""
        if self.request_queue:
            next_req = self.request_queue[0]
            marker = " (OURS)" if next_req.process_id == self.process_id else ""
            print(f"    Queue head: {next_req.process_id} T={next_req.timestamp}{marker} | Total: {len(self.request_queue)}")

def simulate_processing_delay(min_delay=0.5, max_delay=2.0):
    """Simulate server processing time."""
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def simulate_critical_section_work(duration_range=(2, 5)):
    """Simulate work in critical section."""
    duration = random.uniform(*duration_range)
    print(f"    ⚙️  Working in critical section for {duration:.1f}s...")
    time.sleep(duration)

class ExclusionManagerServicer(em_pb2_grpc.ExclusionManagerServicer):
    def __init__(self, process_id, peer_ports, processing_delay_range=(0.5, 2.0)):
        self.clock = LogicalClockWithHistory(process_id)
        self.process_id = process_id
        self.peer_ports = peer_ports
        self.processing_delay_range = processing_delay_range
        self.mutex_state = MutualExclusionState(process_id, peer_ports)

    def RequestEntry(self, request, context):
        print(f"📨 [{self.process_id}] Request from {request.process_id} (T={request.timestamp}, R={request.resource_id})")
        
        # Update logical clock for received message
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        
        # Add request to our queue
        incoming_request = Request(
            timestamp=request.timestamp,
            process_id=request.process_id,
            resource_id=request.resource_id
        )
        self.mutex_state.add_request(incoming_request)
        
        # Simulate processing delay
        simulate_processing_delay(*self.processing_delay_range)
        
        # Send reply
        reply_timestamp = self.clock.tick(f"reply to {request.process_id}")
        
        print(f"📤 [{self.process_id}] Reply to {request.process_id} (T={reply_timestamp})")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message=f"ACK from {self.process_id}"
        )

    def ReleaseEntry(self, request, context):
        print(f"🔓 [{self.process_id}] Release from {request.process_id} (T={request.timestamp}, R={request.resource_id})")
        
        # Update logical clock
        updated_time = self.clock.update(request.timestamp, sender_id=request.process_id)
        
        # Remove the released request from our queue
        self.mutex_state.remove_request(request.process_id, request.resource_id)
        
        # Check if we can now enter critical section
        self._check_and_enter_critical_section()
        
        simulate_processing_delay(*self.processing_delay_range)
        
        reply_timestamp = self.clock.tick(f"ack release from {request.process_id}")
        
        return em_pb2.ReplyMessage(
            timestamp=reply_timestamp,
            process_id=self.process_id,
            granted=True,
            message="Release ACK"
        )

    def GetStatus(self, request, context):
        current_time = self.clock.tick(f"status query")
        
        with self.mutex_state.lock:
            pending = [f"{r.process_id}:{r.resource_id}" for r in self.mutex_state.request_queue]
        
        return em_pb2.StatusResponse(
            process_id=self.process_id,
            in_critical_section=self.mutex_state.in_critical_section,
            current_timestamp=current_time,
            pending_requests=pending
        )
    
    def request_critical_section(self, resource_id: str):
        """Request access to critical section (called by client thread)."""
        print(f"\n🚪 [{self.process_id}] Requesting access to {resource_id}")
        
        # Create our request
        request_timestamp = self.clock.tick(f"request {resource_id}")
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
        print(f"⏳ [{self.process_id}] Waiting for access to {resource_id}...")
        self._wait_for_critical_section_access(resource_id)
        
        # Enter critical section
        self.mutex_state.enter_critical_section(resource_id)
        
        # Simulate work in critical section
        simulate_critical_section_work()
        
        # Exit and release
        self.mutex_state.exit_critical_section()
        self._broadcast_release(resource_id)
        
        print(f"🏁 [{self.process_id}] Completed access to {resource_id}\n")
    
    def _broadcast_request(self, request: Request):
        """Send request to all peer processes."""
        print(f"📡 [{self.process_id}] Broadcasting request to {len(self.peer_ports)} peers")
        
        for peer_port in self.peer_ports:
            try:
                channel = grpc.insecure_channel(f'localhost:{peer_port}')
                stub = em_pb2_grpc.ExclusionManagerStub(channel)
                
                reply = stub.RequestEntry(em_pb2.RequestMessage(
                    timestamp=request.timestamp,
                    process_id=request.process_id,
                    resource_id=request.resource_id
                ))
                
                # Update clock and record reply
                updated_time = self.clock.update(reply.timestamp, sender_id=reply.process_id)
                self.mutex_state.add_reply(request.resource_id, reply.process_id)
                
                channel.close()
                
            except Exception as e:
                print(f"❌ [{self.process_id}] Failed to send request to port {peer_port}: {e}")
    
    def _wait_for_critical_section_access(self, resource_id: str):
        """Wait until we can access the critical section."""
        while not self.mutex_state.can_enter_critical_section(resource_id):
            time.sleep(0.1)
    
    def _check_and_enter_critical_section(self):
        """Check if we can enter critical section for any of our pending requests."""
        with self.mutex_state.lock:
            for resource_id in list(self.mutex_state.our_requests.keys()):
                if self.mutex_state.can_enter_critical_section(resource_id):
                    print(f"✨ [{self.process_id}] Can now access {resource_id}!")
    
    def _broadcast_release(self, resource_id: str):
        """Send release message to all peer processes."""
        print(f"📡 [{self.process_id}] Broadcasting release of {resource_id}")
        
        release_timestamp = self.clock.tick(f"release {resource_id}")
        
        for peer_port in self.peer_ports:
            try:
                channel = grpc.insecure_channel(f'localhost:{peer_port}')
                stub = em_pb2_grpc.ExclusionManagerStub(channel)
                
                reply = stub.ReleaseEntry(em_pb2.ReleaseMessage(
                    timestamp=release_timestamp,
                    process_id=self.process_id,
                    resource_id=resource_id
                ))
                
                updated_time = self.clock.update(reply.timestamp, sender_id=reply.process_id)
                channel.close()
                
            except Exception as e:
                print(f"❌ [{self.process_id}] Failed to send release to port {peer_port}: {e}")

def serve(process_id, port, peers, processing_delay_range=(0.5, 2.0)):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ExclusionManagerServicer(process_id, peers, processing_delay_range)
    em_pb2_grpc.add_ExclusionManagerServicer_to_server(servicer, server)
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"🚀 [{process_id}] Server started on port {port}")
    print(f"    Processing delays: {processing_delay_range[0]}-{processing_delay_range[1]}s")
    print(f"    Peers: {peers}")
    
    # Store servicer globally so client can access it
    global _servicer
    _servicer = servicer
    
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print(f"\n🛑 [{process_id}] Shutting down...")
        print(f"\n📊 [{process_id}] FINAL CLOCK HISTORY:")
        servicer.clock.print_history()
        server.stop(0)

# Global variable to allow client access to servicer
_servicer = None

def get_servicer():
    """Get the current servicer instance (for client use)."""
    return _servicer