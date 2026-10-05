"""Fault injection. Each fault creates a different simulated condition."""
from dataclasses import dataclass

LOSE_COMMUNICATION = "LOSE_COMMUNICATION"
WEAK_SIGNAL = "WEAK_SIGNAL"
ANTENNA_FAILURE = "ANTENNA_FAILURE"
POWER_DROP = "POWER_DROP"
PRIMARY_MODE_FAILURE = "PRIMARY_MODE_FAILURE"
PLANETARY_OBSTRUCTION = "PLANETARY_OBSTRUCTION"


@dataclass(frozen=True)
class FaultInfo:
    label: str
    duration: int        # ticks until it clears by itself (if nobody fixes it earlier)
    description: str


FAULTS = {
    LOSE_COMMUNICATION: FaultInfo("LOSE COMMUNICATION", 60, "Probe radio service stops responding"),
    WEAK_SIGNAL: FaultInfo("WEAK SIGNAL", 40, "Strong interference weakens the signal"),
    ANTENNA_FAILURE: FaultInfo("ANTENNA FAILURE", 100, "Main antenna pointing/health drops sharply"),
    POWER_DROP: FaultInfo("POWER DROP", 80, "Battery collapses; radio has too little power"),
    PRIMARY_MODE_FAILURE: FaultInfo("PRIMARY MODE FAILURE", 70, "Primary communication mode stops working"),
    PLANETARY_OBSTRUCTION: FaultInfo("PLANETARY OBSTRUCTION", 30, "The planet blocks the line of sight"),
}


def inject(fault, probe, env, tick):
    env.active[fault] = tick + FAULTS[fault].duration
    if fault == LOSE_COMMUNICATION:
        probe.comm_service_up = False
    elif fault == WEAK_SIGNAL:
        env.interference = 0.28
    elif fault == ANTENNA_FAILURE:
        probe.antenna_health = 0.15
    elif fault == POWER_DROP:
        probe.battery = 6.0
        probe.power_fault = True
    elif fault == PRIMARY_MODE_FAILURE:
        probe.primary_failed = True
    elif fault == PLANETARY_OBSTRUCTION:
        env.obstruction = 0.05
    else:
        raise ValueError(f"Unknown fault: {fault}")


def _clear(fault, probe, env):
    if fault == LOSE_COMMUNICATION:
        probe.comm_service_up = True
    elif fault == WEAK_SIGNAL:
        env.interference = 1.0
    elif fault == ANTENNA_FAILURE:
        probe.antenna_health = 1.0
    elif fault == POWER_DROP:
        probe.power_fault = False
        probe.battery = max(probe.battery, 45.0)
    elif fault == PRIMARY_MODE_FAILURE:
        probe.primary_failed = False
    elif fault == PLANETARY_OBSTRUCTION:
        env.obstruction = 1.0


def expire(probe, env, tick):
    """Clear faults whose natural duration is over. Returns the cleared names."""
    cleared = []
    for fault, end in list(env.active.items()):
        if tick >= end:
            _clear(fault, probe, env)
            del env.active[fault]
            cleared.append(fault)
    return cleared
