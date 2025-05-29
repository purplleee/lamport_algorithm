# run_processes.py

import subprocess
import sys
import argparse

MAX_PROCESSES = 5
BASE_PORT = 50051

def generate_peer_ports(n, base_port):
    return [base_port + i for i in range(n)]

def launch_process(process_id, port, peers, net_delay="1,3", proc_delay="0.5,2"):
    peer_ports_str = ",".join(str(p) for p in peers)
    command = (f"gnome-terminal -- bash -c '"
               f"python3 process.py --id {process_id} --port {port} --peers {peer_ports_str} "
               f"--net-delay {net_delay} --proc-delay {proc_delay}; exec bash'")
    subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch distributed Lamport clock processes")
    parser.add_argument("num_processes", type=int, nargs="?", default=3, 
                       help="Number of processes to launch (default: 3)")
    parser.add_argument("--net-delay", default="1,3", 
                       help="Network delay range (min,max) in seconds (default: 1,3)")
    parser.add_argument("--proc-delay", default="0.5,2", 
                       help="Processing delay range (min,max) in seconds (default: 0.5,2)")
    
    args = parser.parse_args()
    num_processes = args.num_processes
    
    if num_processes > MAX_PROCESSES:
        print(f"Limit is {MAX_PROCESSES} processes.")
        sys.exit(1)

    ports = generate_peer_ports(num_processes, BASE_PORT)
    
    print(f"Launching {num_processes} processes with:")
    print(f"  Network delays: {args.net_delay}s")
    print(f"  Processing delays: {args.proc_delay}s")
    print(f"  Ports: {ports}")
    print()

    for i in range(num_processes):
        process_id = f"Process-{i+1}"
        port = ports[i]
        peers = ports
        launch_process(process_id, port, peers, args.net_delay, args.proc_delay)
        print(f"Launched {process_id} on port {port}")
    
    print(f"\nAll {num_processes} processes launched!")
    print("Each terminal will show detailed Lamport clock behavior with network delays.")
    print("Press Ctrl+C in any terminal to stop that process.")