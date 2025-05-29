# process.py

import argparse
import threading
import time

from server import serve
from client import run_client

def start_server(process_id, port, peers):
    serve(process_id, port, peers)

def start_client(process_id, port, peers):
    time.sleep(1)
    run_client(process_id, port, peers)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Unique process ID")
    parser.add_argument("--port", required=True, type=int, help="Port this process listens on")
    parser.add_argument("--peers", required=True, help="Comma-separated list of peer ports")

    args = parser.parse_args()
    process_id = args.id
    port = args.port
    peer_ports = [int(p) for p in args.peers.split(",") if int(p) != port]

    server_thread = threading.Thread(target=start_server, args=(process_id, port, peer_ports))
    client_thread = threading.Thread(target=start_client, args=(process_id, port, peer_ports))

    server_thread.start()
    client_thread.start()

    server_thread.join()
    client_thread.join()
