# client.py

import grpc
import em_pb2
import em_pb2_grpc
import time
from logical_clock import LogicalClockWithHistory

def run_client(process_id, port, peer_ports):
    clock = LogicalClockWithHistory(process_id)
    time.sleep(2)  # Wait for servers to start

    print(f"[CLIENT {process_id}] Starting to send requests to peers: {peer_ports}")
    
    for peer_port in peer_ports:
        try:
            # Create connection
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)

            # Increment clock for sending message and get timestamp
            timestamp = clock.tick(f"sending RequestEntry to port {peer_port}")
            resource_id = "resA"

            print(f"[CLIENT {process_id}] Sending RequestEntry to port {peer_port} with timestamp {timestamp}")
            
            # Send request
            response = stub.RequestEntry(em_pb2.RequestMessage(
                timestamp=timestamp,
                process_id=process_id,
                resource_id=resource_id
            ))

            # Update clock based on received response
            clock.update(response.timestamp, sender_id=response.process_id)
            print(f"[CLIENT {process_id}] Received reply from {response.process_id} (port {peer_port}): "
                  f"granted={response.granted}, message='{response.message}', timestamp={response.timestamp}")

            channel.close()

        except grpc.RpcError as e:
            print(f"[CLIENT {process_id}] Failed to connect to port {peer_port}: {e}")
        except Exception as e:
            print(f"[CLIENT {process_id}] Unexpected error with port {peer_port}: {e}")

    # Print the complete history of logical clock events
    clock.print_history()