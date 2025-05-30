# run_processes.py - Enhanced with Mutual Exclusion Support

import subprocess
import sys
import argparse
import time

MAX_PROCESSES = 5
BASE_PORT = 50051

def generate_peer_ports(n, base_port):
    return [base_port + i for i in range(n)]

def launch_process(process_id, port, peers, net_delay="1,3", proc_delay="0.5,2", simple_mode=False):
    peer_ports_str = ",".join(str(p) for p in peers)
    
    simple_flag = "--simple" if simple_mode else ""
    
    command = (f"gnome-terminal -- bash -c '"
               f"python3 process.py --id {process_id} --port {port} --peers {peer_ports_str} "
               f"--net-delay {net_delay} --proc-delay {proc_delay} {simple_flag}; exec bash'")
    subprocess.Popen(command, shell=True)

def demo_mutual_exclusion(num_processes, net_delay, proc_delay):
    """Launch processes in mutual exclusion mode with staggered start times."""
    ports = generate_peer_ports(num_processes, BASE_PORT)
    
    print(f"=== MUTUAL EXCLUSION DEMO ===")
    print(f"Launching {num_processes} processes with mutual exclusion:")
    print(f"  Network delays: {net_delay}s")
    print(f"  Processing delays: {proc_delay}s")
    print(f"  Ports: {ports}")
    print()
    
    for i in range(num_processes):
        process_id = f"Process-{i+1}"
        port = ports[i]
        peers = ports
        
        launch_process(process_id, port, peers, net_delay, proc_delay, simple_mode=False)
        print(f"Launched {process_id} on port {port}")
        
        # Stagger the launches slightly to avoid race conditions
        time.sleep(0.5)
    
    print(f"\nAll {num_processes} processes launched in MUTUAL EXCLUSION mode!")
    print("\nWhat you'll see:")
    print("- Each process will request access to shared resources")
    print("- Only one process can access a resource at a time")
    print("- Lamport timestamps ensure proper ordering")
    print("- Critical section work will be simulated")
    print("\nWatch the terminals to see the mutual exclusion protocol in action!")

def demo_simple_mode(num_processes, net_delay, proc_delay):
    """Launch processes in simple mode (original behavior)."""
    ports = generate_peer_ports(num_processes, BASE_PORT)
    
    print(f"=== SIMPLE MODE DEMO ===")
    print(f"Launching {num_processes} processes in simple mode:")
    print(f"  Network delays: {net_delay}s")
    print(f"  Processing delays: {proc_delay}s")
    print(f"  Ports: {ports}")
    print()

    for i in range(num_processes):
        process_id = f"Process-{i+1}"
        port = ports[i]
        peers = ports
        
        launch_process(process_id, port, peers, net_delay, proc_delay, simple_mode=True)
        print(f"Launched {process_id} on port {port}")
    
    print(f"\nAll {num_processes} processes launched in SIMPLE mode!")
    print("This demonstrates basic Lamport clock synchronization without mutual exclusion.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch distributed Lamport clock processes with mutual exclusion")
    parser.add_argument("num_processes", type=int, nargs="?", default=3, 
                       help="Number of processes to launch (default: 3)")
    parser.add_argument("--net-delay", default="1,3", 
                       help="Network delay range (min,max) in seconds (default: 1,3)")
    parser.add_argument("--proc-delay", default="0.5,2", 
                       help="Processing delay range (min,max) in seconds (default: 0.5,2)")
    parser.add_argument("--simple", action="store_true",
                       help="Run in simple mode (original behavior without mutual exclusion)")
    parser.add_argument("--demo", choices=["mutex", "simple", "both"], default="mutex",
                       help="Demo mode: mutex (mutual exclusion), simple (basic), or both (default: mutex)")
    
    args = parser.parse_args()
    num_processes = args.num_processes
    
    if num_processes > MAX_PROCESSES:
        print(f"Limit is {MAX_PROCESSES} processes.")
        sys.exit(1)
    
    if num_processes < 2:
        print("Need at least 2 processes for meaningful demonstration.")
        sys.exit(1)

    if args.demo == "both":
        print("=== RUNNING BOTH DEMOS ===")
        print("Starting with mutual exclusion demo...")
        demo_mutual_exclusion(num_processes, args.net_delay, args.proc_delay)
        
        input("\nPress Enter to continue with simple mode demo...")
        demo_simple_mode(num_processes, args.net_delay, args.proc_delay)
        
    elif args.demo == "simple" or args.simple:
        demo_simple_mode(num_processes, args.net_delay, args.proc_delay)
    else:
        demo_mutual_exclusion(num_processes, args.net_delay, args.proc_delay)
    
    print("\nPress Ctrl+C in any terminal to stop that process.")
    print("Close terminals when done with the demonstration.")