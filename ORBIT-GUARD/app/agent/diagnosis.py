"""Step 2 of the agent loop: turn raw readings into likely causes (a probability-like score)."""
from app.communication.modes import MODE_SPECS

SERVICE_DOWN = "SERVICE_DOWN"
ANTENNA_DEGRADED = "ANTENNA_DEGRADED"
POWER_LOW = "POWER_LOW"
PRIMARY_FAULT = "PRIMARY_MODE_FAULT"
EXTERNAL_BLOCKAGE = "EXTERNAL_BLOCKAGE"
MODE_MISMATCH = "MODE_MISMATCH"
TRANSIENT = "TRANSIENT"

CAUSE_TEXT = {
    SERVICE_DOWN: "communication service is not responding",
    ANTENNA_DEGRADED: "antenna is degraded",
    POWER_LOW: "battery too low for full transmit power",
    PRIMARY_FAULT: "primary communication mode failed its self-test",
    EXTERNAL_BLOCKAGE: "signal path is blocked or interfered with",
    MODE_MISMATCH: "probe radio is fine but Earth may be listening on another mode",
    TRANSIENT: "no hardware fault found - probably a temporary glitch",
}


def _clip(x):
    return max(0.0, min(1.0, x))


def diagnose(obs):
    """Returns {cause: probability} (sums to 1)."""
    raw = {
        SERVICE_DOWN: 0.95 if not obs.service_up else 0.01,
        ANTENNA_DEGRADED: _clip((0.85 - obs.antenna_health) / 0.7) if obs.antenna_health < 0.85 else 0.01,
        POWER_LOW: _clip((30 - obs.battery_effective) / 30),
        PRIMARY_FAULT: 0.9 if not obs.primary_ok else 0.01,
        EXTERNAL_BLOCKAGE: _clip((0.8 - obs.path_quality) / 0.8),
        TRANSIENT: 0.08,
    }
    # If the current mode could be decoded on this radio but nobody answers,
    # the most likely problem is that Earth is not on the same mode yet.
    spec = MODE_SPECS[obs.comm_mode]
    scan = obs.mode_scan.get(obs.comm_mode, 0.0)
    viable = obs.service_up and scan >= spec.min_signal * 1.2
    raw[MODE_MISMATCH] = 0.7 if (viable and not obs.ack) else 0.02
    total = sum(raw.values())
    return {c: v / total for c, v in raw.items()}


def top_causes(causes, n=2):
    return sorted(causes.items(), key=lambda kv: -kv[1])[:n]
