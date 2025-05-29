import threading

class LogicalClock:
    def __init__(self, initial_time=0):
        self.time = initial_time
        self.lock = threading.Lock()

    def tick(self):
        """Increment clock for a local event."""
        with self.lock:
            self.time += 1
            return self.time

    def update(self, received_time):
        """Update clock based on received timestamp - FIXED VERSION."""
        with self.lock:
            # Lamport clock rule: local_time = max(local_time, received_time) + 1
            # The +1 represents the event of receiving the message
            old_time = self.time
            self.time = max(self.time, received_time) + 1
            return self.time

    def get_time(self):
        """Get current logical time without incrementing."""
        with self.lock:
            return self.time

class LogicalClockWithHistory(LogicalClock):
    def __init__(self, process_id, initial_time=0):
        super().__init__(initial_time)
        self.process_id = process_id
        self.history = []

    def tick(self, event_desc="local event"):
        """Increment clock for local event and record in history."""
        new_time = super().tick()
        with self.lock:
            self.history.append((new_time, f"LOCAL: {event_desc}"))
        return new_time

    def update(self, received_time, sender_id=None):
        """Update clock for received message and record in history."""
        old_time = self.time
        new_time = super().update(received_time)
        
        desc = f"RECEIVED from {sender_id}: msg_ts={received_time}, old_local={old_time}, new_local={new_time}"
        if sender_id is None:
            desc = f"RECEIVED: msg_ts={received_time}, old_local={old_time}, new_local={new_time}"
            
        with self.lock:
            self.history.append((new_time, desc))
        return new_time

    def print_history(self):
        """Print complete history of clock events."""
        with self.lock:
            print(f"\n=== LAMPORT CLOCK HISTORY for {self.process_id} ===")
            for timestamp, desc in self.history:
                print(f"  T={timestamp:2d}: {desc}")
            print(f"Final logical time: {self.time}")
            print("=" * 60)