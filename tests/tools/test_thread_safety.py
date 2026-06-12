import threading

from src.tools import calendar, email
from src.tools.state import get_state, reset_state


def test_thread_local_state_is_independent():
    results = {}

    def thread_fn(thread_id: int, new_subject: str):
        state = get_state()
        original_count = len(state.emails)
        email.send_email("test@atlas.com", new_subject, "body")
        results[thread_id] = {
            "original_count": original_count,
            "final_count": len(get_state().emails),
        }
        reset_state()

    t1 = threading.Thread(target=thread_fn, args=(1, "Thread 1 Subject"))
    t2 = threading.Thread(target=thread_fn, args=(2, "Thread 2 Subject"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    for tid in [1, 2]:
        assert results[tid]["final_count"] == results[tid]["original_count"] + 1


def test_state_mutations_do_not_leak_between_threads():
    barrier = threading.Barrier(2)
    results = {}

    def mutate_and_check(thread_id: int, event_id_to_delete: str):
        get_state()
        barrier.wait()
        calendar.delete_event(event_id=event_id_to_delete)
        results[thread_id] = len(get_state().calendar_events)
        reset_state()

    events = get_state().calendar_events
    event_ids = events["event_id"].tolist()[:2]
    reset_state()

    t1 = threading.Thread(target=mutate_and_check, args=(1, event_ids[0]))
    t2 = threading.Thread(target=mutate_and_check, args=(2, event_ids[1]))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    original_count = len(get_state().calendar_events)
    reset_state()

    for tid in [1, 2]:
        assert results[tid] == original_count - 1


def test_reset_state_restores_original_data():
    state = get_state()
    original_email_count = len(state.emails)
    email.send_email("test@atlas.com", "Test", "Body")
    assert len(get_state().emails) == original_email_count + 1
    reset_state()
    assert len(get_state().emails) == original_email_count
    reset_state()
