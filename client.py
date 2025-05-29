# client.py

import grpc
import em_pb2
import em_pb2_grpc
import time
import random

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = em_pb2_grpc.ExclusionManagerStub(channel)

    timestamp = int(time.time())
    process_id = f"Process-{random.randint(1,100)}"
    resource_id = "resA"

    print(f"[CLIENT] Sending RequestEntry from {process_id}")
    response = stub.RequestEntry(em_pb2.RequestMessage(
        timestamp=timestamp,
        process_id=process_id,
        resource_id=resource_id
    ))
    print(f"[CLIENT] Received reply: granted={response.granted}, message='{response.message}'")

if __name__ == "__main__":
    run()
