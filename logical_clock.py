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
        return self.time

    def get_timestamp_for_send(self):
        """Get current timestamp for sending a message (usually tick first)."""
        return self.tick()

    def sync_with_received_message(self, received_time):
        """Sync on receiving a message with timestamp."""
        return self.update(received_time)

class LogicalClockWithHistory(LogicalClock):
    def __init__(self, process_id, initial_time=0):
        super().__init__(initial_time)
        self.process_id = process_id
        self.history = []

    def tick(self, event_desc="local event"):
        new_time = super().tick()
        self.history.append((new_time, event_desc))
        return new_time

    def update(self, received_time, sender_id=None):
        new_time = super().update(received_time)
        desc = f"update from {sender_id}" if sender_id else "update"
        self.history.append((new_time, desc))
        return new_time

    def print_history(self):
        print(f"History for process {self.process_id}:")
        for timestamp, desc in self.history:
            print(f"  [{timestamp}] {desc}")
