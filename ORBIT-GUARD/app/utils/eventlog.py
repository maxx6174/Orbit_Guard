"""Simple timestamped event log shown on the dashboard."""
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Event:
    tick: int
    clock: str
    source: str     # LINK / EARTH / PROBE / ORBIT-GUARD / FAULT / MISSION
    message: str
    level: str = "info"   # info / warn / bad / good


class EventLog:
    def __init__(self, base=None):
        self.base = base or datetime(2026, 1, 1, 19, 40, 0)
        self.events = []

    def add(self, tick, source, message, level="info"):
        clock = (self.base + timedelta(seconds=tick)).strftime("%H:%M:%S")
        self.events.append(Event(tick, clock, source, message, level))

    def has(self, text):
        return any(text in e.message for e in self.events)

    def save_csv(self, path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tick", "clock", "source", "level", "message"])
            for e in self.events:
                w.writerow([e.tick, e.clock, e.source, e.level, e.message])
