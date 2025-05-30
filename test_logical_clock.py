# test_logical_clock.py
import time
import random
import threading

from logical_clock import LogicalClock, LogicalClockWithHistory
from agrawala_clock import AgrawalaClock

def test_basic_operations():
    print("="*20, "TEST: Basic Operations", "="*20)
    clock = LogicalClock()
    print(f"Initial time: {clock.get_time()}")

    for i in range(5):
        new_time = clock.tick()
        print(f"Tick {i+1}: {new_time}")

    test_timestamps = [3, 8, 6, 12, 5]
    for i, ts in enumerate(test_timestamps):
        updated_time = clock.update(ts)
        print(f"Update {i+1} with received {ts}: {updated_time}")

def test_lamport_rules():
    print("="*20, "TEST: Lamport Rules", "="*20)
    clock = LogicalClock(0)
    times = [clock.tick() for _ in range(3)]
    print(f"Ticks sequence: {times}")

    print("Update with larger timestamp (10):")
    print(clock.update(10))

    print("Update with smaller timestamp (5):")
    print(clock.update(5))

def test_concurrent_processes():
    print("="*20, "TEST: Concurrent Processes", "="*20)
    pA = LogicalClockWithHistory("A", 0)
    pB = LogicalClockWithHistory("B", 0)
    pC = LogicalClockWithHistory("C", 0)

    pA.tick("Start A")
    pB.tick("Start B")
    pB.tick("Local B")
    pC.tick("Start C")

    ts = pA.tick("Send A->B")
    pB.update(ts, "A")

    ts = pB.tick("Send B->C")
    pC.update(ts, "B")

    ts = pC.tick("Send C->A")
    pA.update(ts, "C")

    ts = pA.tick("Broadcast A->all")
    pB.update(ts, "A")
    pC.update(ts, "A")

    pA.print_history()
    pB.print_history()
    pC.print_history()

def test_thread_safety():
    print("="*20, "TEST: Thread Safety", "="*20)
    clock = LogicalClock()
    results = []
    num_threads = 5
    ops_per_thread = 20

    def worker(tid):
        for _ in range(ops_per_thread):
            if random.choice([True, False]):
                val = clock.tick()
                results.append(("tick", val, tid))
            else:
                val = clock.update(random.randint(1, 50))
                results.append(("update", val, tid))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads: t.start()
    for t in threads: t.join()

    print(f"Final clock time: {clock.get_time()}")
    print(f"Total operations: {len(results)}")

def test_agrawala_logic():
    print("="*20, "TEST: Agrawala Clock", "="*20)
    from agrawala_clock import AgrawalaClock

    print("Creating clocks...")
    pA = AgrawalaClock("A")
    pB = AgrawalaClock("B")

    print("A requests CS")
    tsA = pA.request_critical_section()
    print(f"A requests CS at {tsA}")

    print("B receives A's request")
    pB.sync_with_received_message(tsA, "A")

    print("B requests CS")
    tsB = pB.request_critical_section()
    print(f"B requests CS at {tsB}")

    print("A receives B's request")
    pA.sync_with_received_message(tsB, "B")

    print("Checking if B should defer reply to A")
    should_B_defer = pB.should_defer_reply(tsA, "A")
    print(f"B should defer reply to A? {should_B_defer}")

    print("Checking if A should defer reply to B")
    should_A_defer = pA.should_defer_reply(tsB, "B")
    print(f"A should defer reply to B? {should_A_defer}")

    print("A defers reply to B")
    pA.defer_reply_to("B")
    print(f"A's deferred replies: {pA.get_deferred_replies()}")

    print("A releases critical section")
    pA.release_critical_section()
    print(f"A released CS. Deferred replies after release: {pA.get_deferred_replies()}")

    print("Printing histories")
    pA.print_history()
    pB.print_history()

def run_all_tests():
    test_basic_operations()
    test_lamport_rules()
    test_concurrent_processes()
    test_thread_safety()
    test_agrawala_logic()
    print("All tests done.")

if __name__ == "__main__":
    run_all_tests()
