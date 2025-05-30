# process.py - Enhanced with Mutual Exclusion Support

import argparse
import threading
import time
import signal
import sys

from server import serve
from client import run_client, run_simple_client

def start_server(process_id, port, peers, processing_delay_range):
    """Start the gRPC server for this process."""
    serve(process_id, port, peers, processing_delay_range)

def start_client(process_id, port, peers, network_delay_range, simple_mode=False):
    """Start the client that demonstrates mutual exclusion or simple requests."""
    # Wait longer to ensure all servers are up
    time.sleep(6)
    
    if simple_mode:
        print(f"[PROCESS {process_id}] Starting in SIMPLE mode (original behavior)")
        run_simple_client(process_id, port, peers, network_delay_range)
    else:
        print(f"[PROCESS {process_id}] Starting in MUTUAL EXCLUSION mode")
        run_client(process_id, port, peers, network_delay_range)

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
    parser.add_argument("--net-delay", default="1,3", help="Network delay range (min,max) in seconds")
    parser.add_argument("--proc-delay", default="0.5,2", help="Processing delay range (min,max) in seconds")
    parser.add_argument("--simple", action="store_true", help="Run in simple mode (original behavior without mutex)")

    args = parser.parse_args()
    process_id = args.id
    port = args.port
    simple_mode = args.simple
    
    # Parse peer ports and exclude own port
    peer_ports = [int(p) for p in args.peers.split(",") if int(p) != port]
    
    # Parse delay ranges
    net_delays = [float(x) for x in args.net_delay.split(",")]
    proc_delays = [float(x) for x in args.proc_delay.split(",")]
    
    network_delay_range = (net_delays[0], net_delays[1])
    processing_delay_range = (proc_delays[0], proc_delays[1])
    
    mode_str = "SIMPLE" if simple_mode else "MUTUAL EXCLUSION"
    
    print(f"[PROCESS {process_id}] Starting in {mode_str} mode on port {port}")
    print(f"[PROCESS {process_id}] Peer ports: {peer_ports}")
    print(f"[PROCESS {process_id}] Network delays: {network_delay_range[0]}-{network_delay_range[1]}s")
    print(f"[PROCESS {process_id}] Processing delays: {processing_delay_range[0]}-{processing_delay_range[1]}s")

    # Create and start threads
    server_thread = threading.Thread(
        target=start_server, 
        args=(process_id, port, peer_ports, processing_delay_range)
    )
    client_thread = threading.Thread(
        target=start_client, 
        args=(process_id, port, peer_ports, network_delay_range, simple_mode)
    )

    # Set threads as daemon so they exit when main program exits
    server_thread.daemon = True
    client_thread.daemon = True

    server_thread.start()
    client_thread.start()

    try:
        # Wait for client to finish (it will terminate after sending messages)
        client_thread.join()
        print(f"\n[PROCESS {process_id}] Client finished, keeping server running...")
        print(f"[PROCESS {process_id}] Press Ctrl+C to shutdown server...")
        
        # Keep server running
        server_thread.join()
    except KeyboardInterrupt:
        print(f"[PROCESS {process_id}] Interrupted, shutting down...")
        sys.exit(0)