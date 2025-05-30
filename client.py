# client.py - Clean Enhanced Mutual Exclusion Client

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
    time.sleep(delay)

def run_client(process_id, port, peer_ports, network_delay_range=(1, 3)):
    """Run client that demonstrates mutual exclusion."""
    
    # Import here to avoid circular imports
    from server import get_servicer
    
    time.sleep(5)  # Wait for all servers to be ready
    
    min_delay, max_delay = network_delay_range
    print(f"\n🎮 [{process_id}] MUTUAL EXCLUSION CLIENT STARTING")
    print(f"    Network delays: {min_delay}-{max_delay}s")
    print(f"    Coordinating with {len(peer_ports)} peers")
    
    # Get the servicer to access mutual exclusion functionality
    servicer = get_servicer()
    if not servicer:
        print(f"❌ [{process_id}] ERROR: Could not get servicer instance")
        return
    
    # REDUCED: Only one critical section request
    resources = ["ResourceA"]  # Single request instead of 3
    
    for i, resource_id in enumerate(resources):
        try:
            print(f"\n📋 [{process_id}] === REQUEST {i+1}/{len(resources)} ===")
            
            # Request critical section access - this handles the entire protocol
            servicer.request_critical_section(resource_id)
            
        except Exception as e:
            print(f"❌ [{process_id}] Error during critical section request: {e}")
    
    # Optional: Query status from peers (also reduced)
    print(f"\n📊 [{process_id}] === STATUS QUERIES ===")
    
    # REDUCED: Only query 1 peer instead of 2
    status_queries = min(1, len(peer_ports))
    selected_ports = random.sample(peer_ports, status_queries) if peer_ports else []
    
    for peer_port in selected_ports:
        try:
            print(f"🔍 [{process_id}] Querying status from port {peer_port}")
            
            simulate_network_delay(min_delay, max_delay)
            
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)
            
            send_time = servicer.clock.tick(f"status query to {peer_port}")
            
            response = stub.GetStatus(em_pb2.StatusRequest(process_id=process_id))
            
            simulate_network_delay(min_delay, max_delay)
            
            updated_time = servicer.clock.update(response.current_timestamp, 
                                               sender_id=response.process_id)
            
            status = "🔒 IN CS" if response.in_critical_section else "🔓 FREE"
            print(f"    {response.process_id}: {status} | Clock: {response.current_timestamp} | Queue: {len(response.pending_requests)}")
            
            channel.close()
            
        except Exception as e:
            print(f"❌ [{process_id}] Status query failed for port {peer_port}: {e}")
    
    # Final summary
    print(f"\n🏆 [{process_id}] === DEMO COMPLETE ===")
    print(f"    Completed {len(resources)} critical section requests")
    print(f"    Queried {len(selected_ports)} peers for status")
    
    # Print final clock history
    print(f"\n📊 [{process_id}] FINAL CLOCK HISTORY:")
    servicer.clock.print_history()

def run_simple_client(process_id, port, peer_ports, network_delay_range=(1, 3)):
    """Simplified client for basic testing without mutual exclusion."""
    
    clock = LogicalClockWithHistory(process_id)
    time.sleep(2)

    min_delay, max_delay = network_delay_range
    print(f"\n🔧 [{process_id}] SIMPLE CLIENT STARTING")
    print(f"    Network delays: {min_delay}-{max_delay}s")
    print(f"    Sending basic requests to {len(peer_ports)} peers")
    
    for i, peer_port in enumerate(peer_ports):
        try:
            print(f"\n📤 [{process_id}] Request {i+1}/{len(peer_ports)} to port {peer_port}")
            
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)

            send_timestamp = clock.tick(f"request to {peer_port}")
            resource_id = "TestResource"

            print(f"    Sending at T={send_timestamp}")
            
            # Network delay
            simulate_network_delay(min_delay, max_delay)
            
            # Some local work during delay
            local_work_events = random.randint(0, 2)
            for j in range(local_work_events):
                work_time = clock.tick(f"local work {j+1}")
                print(f"    Local work at T={work_time}")
            
            # Send request
            actual_send_time = clock.tick(f"send to {peer_port}")
            
            response = stub.RequestEntry(em_pb2.RequestMessage(
                timestamp=actual_send_time,
                process_id=process_id,
                resource_id=resource_id
            ))

            # Network delay for response
            simulate_network_delay(min_delay, max_delay)
            
            # Update clock for received response
            old_time = clock.get_time()
            updated_time = clock.update(response.timestamp, sender_id=response.process_id)
            
            print(f"    📨 Reply from {response.process_id}: T={response.timestamp}")
            print(f"    Clock: {old_time} → {updated_time}")
            
            channel.close()
            
            # Processing delay between requests
            if i < len(peer_ports) - 1:
                processing_delay = random.uniform(0.5, 1.5)
                time.sleep(processing_delay)
                processing_time = clock.tick(f"processing")

        except grpc.RpcError as e:
            print(f"❌ [{process_id}] Failed to connect to port {peer_port}: {e}")
        except Exception as e:
            print(f"❌ [{process_id}] Unexpected error with port {peer_port}: {e}")

    print(f"\n🏁 [{process_id}] SIMPLE CLIENT COMPLETE")
    print(f"\n📊 [{process_id}] FINAL CLOCK HISTORY:")
    clock.print_history()