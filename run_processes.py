# run_processes.py

import subprocess
import sys

MAX_PROCESSES = 5
BASE_PORT = 50051

def generate_peer_ports(n, base_port):
    return [base_port + i for i in range(n)]

def launch_process(process_id, port, peers):
    peer_ports_str = ",".join(str(p) for p in peers)
    command = f"gnome-terminal -- bash -c 'python3 process.py --id {process_id} --port {port} --peers {peer_ports_str}; exec bash'"
    subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    num_processes = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if num_processes > MAX_PROCESSES:
        print(f"Limit is {MAX_PROCESSES} processes.")
        sys.exit(1)

    ports = generate_peer_ports(num_processes, BASE_PORT)

    for i in range(num_processes):
        process_id = f"Process-{i+1}"
        port = ports[i]
        peers = ports
        launch_process(process_id, port, peers)
