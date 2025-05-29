# client.py

import grpc
import em_pb2
import em_pb2_grpc
import time

def run_client(process_id, port, peer_ports):
    time.sleep(2)  # Give the server time to start

    for peer_port in peer_ports:
        try:
            channel = grpc.insecure_channel(f'localhost:{peer_port}')
            stub = em_pb2_grpc.ExclusionManagerStub(channel)

            timestamp = int(time.time())
            resource_id = "resA"

            print(f"[CLIENT {process_id}] Sending RequestEntry to port {peer_port}")
            response = stub.RequestEntry(em_pb2.RequestMessage(
                timestamp=timestamp,
                process_id=process_id,
                resource_id=resource_id
            ))
            print(f"[CLIENT {process_id}] Received from port {peer_port}: granted={response.granted}, message='{response.message}'")

        except grpc.RpcError as e:
            print(f"[CLIENT {process_id}] Failed to connect to port {peer_port}: {e}")

if __name__ == "__main__":
    run_client("Manual-Client", 50051, [50052])
