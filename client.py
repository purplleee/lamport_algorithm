# client.py - Enhanced with Mutual Exclusion

import grpc
import em_pb2
import em_pb2_grpc
import time
import random
import threading
from logical_clock import LogicalClockWithHistory

def simulate_network_delay(min_delay=1, max_delay=3):
    """Simulate network delay between min_delay and max_delay seconds."""
    delay = random.uniform(min_delay, max_delay)
    print(f"    [NETWORK] Simulating network delay: {delay:.2f}s")
    time.sleep(delay)

def run_client(process_id, port, peer_ports, network_delay_range=(1, 3)):
    """Run client that demonstrates mutual exclusion."""
    
    # Import here to avoid circular imports
    from server import get_servicer
    
    time.sleep(5)  # Wait for all servers to be ready
    
    min_delay, max_delay = network_delay_range
    print(f"\n[CLIENT {process_id}] ===== MUTUAL EXCLUSION DEMO STARTING =====")
    print(f"[CLIENT {process_id}] Network delays: {min_delay}-{max_delay}s")
    print(f"[CLIENT {process_id}] Will coordinate with peers on ports: {peer_ports}")
    
    # Get the servicer to access mutual exclusion functionality
    servicer = get_servicer()
    if not servicer:
        print(f"[CLIENT {process_id}] ERROR: Could not get servicer instance")
        return
    
    # Simulate multiple critical section requests
    resources = ["ResourceA", "ResourceB", "ResourceA"]  # Test same resource multiple times
    
    for i, resource_id in enumerate(resources):
        try:
            print(f"\n[CLIENT {process_id}] ===== Attempt {i+1}/{len(resources)} =====")
            print(f"[CLIENT {process_id}] Requesting access to {resource_id}")
            
            # Add some random delay between requests
            if i > 0:
                delay = random.uniform(2, 5)
                print(f"[CLIENT {process_id}] Waiting {delay:.2f}s before next request...")
                time.sleep(delay)
            
            # Request critical section access
            # This will handle the entire mutual exclusion protocol
            servicer.request_critical_section(resource_id)
            
            print(f"[CLIENT {process_id}] Completed critical section for {resource_id}")
            
        except Exception as e:
            print(f"[CLIENT {process_id}] Error during critical section request: {e}")
    
    # Optional: Demonstrate some additional network communication
    print(f"\n[CLIENT {process_id}] ===== Additional Network Communication =====")
    
    # Query status from a few peers
    status_queries = min(2, len(peer_ports))  # Query up to 2 peers
    selected_ports = random.sample(peer_ports, status_queries) if peer_ports else []
    
    for peer_port in selected_ports:
        try:
            print(f"[CLIENT {process_id}] Querying status from port {peer_port}")
            
            # Simulate network delay
            simulate_network_delay(min_delay, max_delay)
            
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)
            
            # Update our clock for sending status request
            send_time = servicer.clock.tick(f"sending status query to port {peer_port}")
            
            response = stub.GetStatus(em_pb2.StatusRequest(
                process_id=process_id
            ))
            
            # Simulate network delay for response
            simulate_network_delay(min_delay, max_delay)
            
            # Update clock for received response
            updated_time = servicer.clock.update(response.current_timestamp, 
                                               sender_id=response.process_id)
            
            print(f"[CLIENT {process_id}] Status response from {response.process_id}:")
            print(f"    In critical section: {response.in_critical_section}")
            print(f"    Remote timestamp: {response.current_timestamp}")
            print(f"    Our clock updated to: {updated_time}")
            print(f"    Pending requests: {response.pending_requests}")
            
            channel.close()
            
        except grpc.RpcError as e:
            print(f"[CLIENT {process_id}] Failed to query status from port {peer_port}: {e}")
        except Exception as e:
            print(f"[CLIENT {process_id}] Unexpected error querying port {peer_port}: {e}")
    
    # Final summary
    print(f"\n[CLIENT {process_id}] ===== MUTUAL EXCLUSION DEMO COMPLETE =====")
    print(f"[CLIENT {process_id}] Successfully completed {len(resources)} critical section requests")
    print(f"[CLIENT {process_id}] Queried status from {len(selected_ports)} peers")
    
    # Print final clock history
    servicer.clock.print_history()

def run_simple_client(process_id, port, peer_ports, network_delay_range=(1, 3)):
    """Alternative simpler client for basic testing (your original functionality)."""
    
    clock = LogicalClockWithHistory(process_id)
    time.sleep(2)  # Initial wait for servers to start

    min_delay, max_delay = network_delay_range
    print(f"[CLIENT {process_id}] Starting SIMPLE mode with network delays: {min_delay}-{max_delay}s")
    print(f"[CLIENT {process_id}] Will send basic requests to peers: {peer_ports}")
    
    for i, peer_port in enumerate(peer_ports):
        try:
            print(f"\n[CLIENT {process_id}] ===== Simple Request {i+1}/{len(peer_ports)} =====")
            
            # Create connection
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)

            # Prepare message
            send_timestamp = clock.tick(f"preparing to send RequestEntry to port {peer_port}")
            resource_id = "TestResource"

            print(f"[CLIENT {process_id}] Sending basic RequestEntry to port {peer_port} with timestamp {send_timestamp}")
            
            # Network delay
            simulate_network_delay(min_delay, max_delay)
            
            # Local work during delay
            local_work_events = random.randint(0, 2)
            for j in range(local_work_events):
                work_time = clock.tick(f"local work during network delay (step {j+1})")
                print(f"[CLIENT {process_id}] Local work at time {work_time}")
            
            # Send request
            actual_send_time = clock.tick(f"sending message to port {peer_port}")
            print(f"[CLIENT {process_id}] Message sent at logical time: {actual_send_time}")
            
            response = stub.RequestEntry(em_pb2.RequestMessage(
                timestamp=actual_send_time,
                process_id=process_id,
                resource_id=resource_id
            ))

            # Network delay for response
            simulate_network_delay(min_delay, max_delay)
            
            # Update clock for received response
            current_time_before = clock.get_time()
            updated_time = clock.update(response.timestamp, sender_id=response.process_id)
            
            print(f"[CLIENT {process_id}] Received reply from {response.process_id}:")
            print(f"    Response timestamp: {response.timestamp}")
            print(f"    Local time before: {current_time_before}")
            print(f"    Local time after: {updated_time}")
            print(f"    Message: '{response.message}'")
            
            channel.close()
            
            # Processing delay between requests
            if i < len(peer_ports) - 1:
                processing_delay = random.uniform(0.5, 1.5)
                print(f"[CLIENT {process_id}] Processing delay: {processing_delay:.2f}s")
                time.sleep(processing_delay)
                
                processing_time = clock.tick(f"local processing between requests")
                print(f"[CLIENT {process_id}] Local processing at time: {processing_time}")

        except grpc.RpcError as e:
            print(f"[CLIENT {process_id}] Failed to connect to port {peer_port}: {e}")
        except Exception as e:
            print(f"[CLIENT {process_id}] Unexpected error with port {peer_port}: {e}")

    print(f"\n[CLIENT {process_id}] ===== SIMPLE CLIENT FINAL HISTORY =====")
    clock.print_history()