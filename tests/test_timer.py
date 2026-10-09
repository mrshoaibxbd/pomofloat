from pomofloat.timer import TimerEngine


def test_countdown_and_fourth_long_break():
    timer = TimerEngine({"work": 10, "short": 2, "long": 3})
    timer.start(100.0)
    assert not timer.update(109.9)
    assert timer.update(110.0)
    assert timer.mode == "short"
    timer.completed_sessions = 3
    timer.set_mode("work")
    timer.start(0)
    assert timer.update(10)
    assert timer.mode == "long"


def test_pause_and_skip():
    timer = TimerEngine({"work": 60})
    timer.start(10)
    timer.pause(25)
    assert timer.remaining == 45
    timer.skip()
    assert timer.mode == "short"


def test_zero_remaining_restarts_with_current_duration():
    timer = TimerEngine({"work": 10}, remaining=0)
    timer.start(5)
    assert timer.deadline == 15


def test_custom_cycle_length():
    timer = TimerEngine({"work": 1, "short": 1, "long": 1}, cycle_length=2)
    timer.completed_sessions = 1
    timer.start(0)
    assert timer.update(1)
    assert timer.mode == "long"
