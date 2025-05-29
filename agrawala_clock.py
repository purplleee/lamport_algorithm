import threading

class AgrawalaClock:
    def __init__(self, process_id, initial_time=0):
        self.process_id = process_id
        self.time = initial_time
        self.lock = threading.RLock()  # 🔄 FIXED HERE
        self.history = []

        self.request_timestamp = None
        self.deferred_replies = set()


    def tick(self, event_desc="local event"):
        with self.lock:
            self.time += 1
            self.history.append((self.time, event_desc))
            return self.time

    def update(self, received_time, sender_id=None):
        with self.lock:
            self.time = max(self.time, received_time) + 1
            desc = f"update from {sender_id}" if sender_id else "update"
            self.history.append((self.time, desc))
            return self.time

    def get_time(self):
        with self.lock:
            return self.time

    def get_timestamp_for_send(self):
        return self.tick("send event")

    def sync_with_received_message(self, received_time, sender_id=None):
        return self.update(received_time, sender_id)

    def request_critical_section(self):
        with self.lock:
            self.request_timestamp = self.tick("request critical section")
            return self.request_timestamp

    def release_critical_section(self):
        with self.lock:
            self.history.append((self.time, "release critical section"))
            self.request_timestamp = None
            self.deferred_replies.clear()

    def should_defer_reply(self, other_timestamp, other_process_id):
        with self.lock:
            if self.request_timestamp is None:
                return False
            my_request = (self.request_timestamp, self.process_id)
            other_request = (other_timestamp, other_process_id)
            return my_request < other_request

    def defer_reply_to(self, process_id):
        with self.lock:
            self.deferred_replies.add(process_id)

    def get_deferred_replies(self):
        with self.lock:
            return list(self.deferred_replies)

    def print_history(self):
        print(f"History for process {self.process_id}:")
        for timestamp, desc in self.history:
            print(f"  [{timestamp}] {desc}")
