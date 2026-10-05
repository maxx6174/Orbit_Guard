"""Scripted hackathon demo: normal mission -> fault -> recovery -> data transfer."""
from app.simulation import faults as F

DEMO_FAULT = F.ANTENNA_FAILURE      # a clear story: the main antenna fails, backup mode saves the day
DEMO_FAULT_TICK = 15

DEMO_STEPS = [
    "Normal communication",
    "Mission data being sent",
    "Communication failure",
    "Earth detects failure",
    "Probe detects failure",
    "ORBIT-GUARD starts recovery",
    "Earth tries recovery",
    "Probe tries recovery",
    "Communication restored",
    "Stored data transferred",
    "Mission back to normal",
]


def advance(engine, fault=DEMO_FAULT):
    """Advance one tick and inject the demo fault on schedule."""
    if engine.tick + 1 == DEMO_FAULT_TICK and engine.fault_tick is None:
        engine.step()
        engine.inject_fault(fault)
        return
    engine.step()


def milestones(engine):
    """Which of the 11 demo steps have happened so far (list of bools)."""
    has = engine.log.has
    return [
        engine.tick >= 3 and len(engine.earth.received) > 0,
        len(engine.earth.received) >= 5,
        engine.fault_tick is not None,
        has("Earth detected connection loss"),
        engine.agent is not None and has("ORBIT-GUARD detected"),
        engine.agent is not None and has("Entering COMMUNICATION RECOVERY MODE"),
        engine.earth.attempts >= 1,
        engine.probe_attempts >= 1,
        engine.restored_at is not None,
        engine.transfer_done or (engine.restored_at is not None and engine.backlog <= 2),
        engine.finished() and engine.display_state() == "CONNECTED",
    ]
