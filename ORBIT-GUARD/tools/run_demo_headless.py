"""Run the full demo without the dashboard and print the event log:  python tools/run_demo_headless.py"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.simulation.demo import DEMO_STEPS, advance, milestones  # noqa: E402
from app.simulation.engine import EARTH_AGENT, EARTH_ONLY, MODE_LABELS, Engine  # noqa: E402

for mode in (EARTH_ONLY, EARTH_AGENT):
    eng = Engine(mode, seed=7)
    while eng.tick < 300 and not (eng.fault_tick and eng.finished()):
        advance(eng)
    print(f"\n===== {MODE_LABELS[mode]} =====")
    for ev in eng.log.events:
        print(f"{ev.clock} [{ev.source}] {ev.message}")
    print("Demo steps reached:", sum(milestones(eng)), "of", len(DEMO_STEPS))
    print("Metrics:", eng.metrics())
    os.makedirs(os.path.join(ROOT, "data", "logs"), exist_ok=True)
    eng.log.save_csv(os.path.join(ROOT, "data", "logs", f"demo_{mode}.csv"))
