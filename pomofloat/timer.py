"""Clock-independent Pomodoro timer state."""
from dataclasses import dataclass, field


DEFAULT_DURATIONS = {"work": 1500, "short": 300, "long": 900}


@dataclass
class TimerEngine:
    durations: dict[str, int] = field(default_factory=lambda: DEFAULT_DURATIONS.copy())
    mode: str = "work"
    remaining: float | None = None
    completed_sessions: int = 0
    cycle_length: int = 4
    running: bool = False
    deadline: float | None = None

    def __post_init__(self):
        self.durations = {**DEFAULT_DURATIONS, **self.durations}
        if self.mode not in self.durations:
            self.mode = "work"
        if self.remaining is None:
            self.remaining = float(self.durations[self.mode])

    @property
    def duration(self) -> int:
        return self.durations[self.mode]

    def start(self, now: float):
        if self.remaining <= 0:
            self.remaining = float(self.duration)
        self.deadline = now + self.remaining
        self.running = True

    def pause(self, now: float):
        if self.running and self.deadline is not None:
            self.remaining = max(0.0, self.deadline - now)
        self.running = False
        self.deadline = None

    def reset(self):
        self.running = False
        self.deadline = None
        self.remaining = float(self.duration)

    def set_mode(self, mode: str):
        if mode not in self.durations:
            raise ValueError(f"Unknown timer mode: {mode}")
        self.running = False
        self.deadline = None
        self.mode = mode
        self.remaining = float(self.duration)

    def skip(self):
        self.set_mode("short" if self.mode == "work" else "work")

    def update(self, now: float) -> bool:
        if not self.running or self.deadline is None:
            return False
        self.remaining = max(0.0, self.deadline - now)
        if self.remaining > 0:
            return False
        self.running = False
        self.deadline = None
        if self.mode == "work":
            self.completed_sessions += 1
            next_mode = "long" if self.completed_sessions % self.cycle_length == 0 else "short"
        else:
            next_mode = "work"
        self.set_mode(next_mode)
        return True
