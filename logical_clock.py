# logical_clock.py
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
        """Update clock based on received timestamp."""
        with self.lock:
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
        new_time = super().tick()
        with self.lock:
            self.history.append((new_time, event_desc))
        return new_time

    def update(self, received_time, sender_id=None):
        new_time = super().update(received_time)
        desc = f"received message from {sender_id} (ts: {received_time})" if sender_id else f"update (received ts: {received_time})"
        with self.lock:
            self.history.append((new_time, desc))
        return new_time

    def print_history(self):
        with self.lock:
            print(f"\n=== History for process {self.process_id} ===")
            for timestamp, desc in self.history:
                print(f"  [{timestamp}] {desc}")
            print(f"Final logical time: {self.time}")
            print("=" * 40)