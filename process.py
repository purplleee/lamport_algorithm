# process.py

import argparse
import threading
import time
import signal
import sys

from server import serve
from client import run_client

def start_server(process_id, port, peers):
    """Start the gRPC server for this process."""
    serve(process_id, port, peers)

def start_client(process_id, port, peers):
    """Start the client that sends requests to peers."""
    # Wait a bit longer to ensure all servers are up
    time.sleep(3)
    run_client(process_id, port, peers)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print(f"\n[PROCESS] Received interrupt signal, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description="Lamport Clock Mutual Exclusion Process")
    parser.add_argument("--id", required=True, help="Unique process ID")
    parser.add_argument("--port", required=True, type=int, help="Port this process listens on")
    parser.add_argument("--peers", required=True, help="Comma-separated list of peer ports")

    args = parser.parse_args()
    process_id = args.id
    port = args.port
    
    # Parse peer ports and exclude own port
    peer_ports = [int(p) for p in args.peers.split(",") if int(p) != port]
    
    print(f"[PROCESS {process_id}] Starting on port {port}")
    print(f"[PROCESS {process_id}] Peer ports: {peer_ports}")

    # Create and start threads
    server_thread = threading.Thread(target=start_server, args=(process_id, port, peer_ports))
    client_thread = threading.Thread(target=start_client, args=(process_id, port, peer_ports))

    # Set threads as daemon so they exit when main program exits
    server_thread.daemon = True
    client_thread.daemon = True

    server_thread.start()
    client_thread.start()

    try:
        # Wait for client to finish (it will terminate after sending messages)
        client_thread.join()
        print(f"[PROCESS {process_id}] Client finished, keeping server running...")
        
        # Keep server running
        server_thread.join()
    except KeyboardInterrupt:
        print(f"[PROCESS {process_id}] Interrupted, shutting down...")
        sys.exit(0)