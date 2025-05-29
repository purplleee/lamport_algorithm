# client.py 

import grpc
import em_pb2
import em_pb2_grpc
import time
import random
from logical_clock import LogicalClockWithHistory

def simulate_network_delay(min_delay=1, max_delay=3):
    """Simulate network delay between min_delay and max_delay seconds."""
    delay = random.uniform(min_delay, max_delay)
    print(f"    [NETWORK] Simulating network delay: {delay:.2f}s")
    time.sleep(delay)

def run_client(process_id, port, peer_ports, network_delay_range=(1, 3)):
    clock = LogicalClockWithHistory(process_id)
    time.sleep(2)  # Initial wait for servers to start

    min_delay, max_delay = network_delay_range
    print(f"[CLIENT {process_id}] Starting with network delays: {min_delay}-{max_delay}s")
    print(f"[CLIENT {process_id}] Will send requests to peers: {peer_ports}")
    
    for i, peer_port in enumerate(peer_ports):
        try:
            print(f"\n[CLIENT {process_id}] ===== Request {i+1}/{len(peer_ports)} =====")
            
            # Create connection
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)

            # FIXED: Increment clock for "preparing to send" event
            send_timestamp = clock.tick(f"preparing to send RequestEntry to port {peer_port}")
            resource_id = "resA"

            print(f"[CLIENT {process_id}] Sending RequestEntry to port {peer_port} with timestamp {send_timestamp}")
            
            # FIXED: Network delay should be simulated but not affect the logical clock
            # The delay represents the time the message spends in transit
            simulate_network_delay(min_delay, max_delay)
            
            # During network delay, we might do some local work
            # This represents concurrent local processing
            local_work_events = random.randint(0, 2)
            for j in range(local_work_events):
                work_time = clock.tick(f"local work during network delay (step {j+1})")
                print(f"[CLIENT {process_id}] Local work at time {work_time}")
            
            # Send request (this is when the message actually gets sent)
            actual_send_time = clock.tick(f"actually sending message to port {peer_port}")
            print(f"[CLIENT {process_id}] Message actually sent at logical time: {actual_send_time}")
            
            # FIXED: Use the actual send time as the timestamp in the message
            response = stub.RequestEntry(em_pb2.RequestMessage(
                timestamp=actual_send_time,  # Use the time when we actually send
                process_id=process_id,
                resource_id=resource_id
            ))

            # FIXED: Network delay for response (message in transit)
            print(f"    [NETWORK] Simulating response network delay...")
            simulate_network_delay(min_delay, max_delay)
            
            # FIXED: Update clock based on received response (single operation)
            current_time_before = clock.get_time()
            updated_time = clock.update(response.timestamp, sender_id=response.process_id)
            
            print(f"[CLIENT {process_id}] Received reply from {response.process_id} (port {peer_port}):")
            print(f"    Response timestamp: {response.timestamp}")
            print(f"    Local time before update: {current_time_before}")
            print(f"    Local time after update: {updated_time}")
            print(f"    Message: '{response.message}'")
            print(f"    Granted: {response.granted}")

            channel.close()
            
            # Add some processing time between requests
            if i < len(peer_ports) - 1:  # Not the last request
                processing_delay = random.uniform(0.5, 1.5)
                print(f"[CLIENT {process_id}] Processing delay before next request: {processing_delay:.2f}s")
                time.sleep(processing_delay)
                
                # FIXED: This represents actual local processing work
                processing_time = clock.tick(f"local processing between requests")
                print(f"[CLIENT {process_id}] Local processing completed at time: {processing_time}")

        except grpc.RpcError as e:
            print(f"[CLIENT {process_id}] Failed to connect to port {peer_port}: {e}")
        except Exception as e:
            print(f"[CLIENT {process_id}] Unexpected error with port {peer_port}: {e}")

    # Print the complete history of logical clock events
    print(f"\n[CLIENT {process_id}] ===== FINAL LAMPORT CLOCK HISTORY =====")
    clock.print_history()