"""The recovery actions ORBIT-GUARD can take and how they change the simulated probe."""
from app.communication.modes import BACKUP, LOW_RATE, PRIMARY

RETRY_COMM = "RETRY_COMM"
SWITCH_BACKUP = "SWITCH_BACKUP"
SWITCH_LOW_RATE = "SWITCH_LOW_RATE"
SWITCH_PRIMARY = "SWITCH_PRIMARY"
ADJUST_SIGNAL = "ADJUST_SIGNAL"
RESTART_SERVICE = "RESTART_SERVICE"
WAIT_WINDOW = "WAIT_WINDOW"
REDUCE_LOAD = "REDUCE_LOAD"
STORE_DATA = "STORE_DATA"
MONITOR = "MONITOR"
REPORT_STATUS = "REPORT_STATUS"

# label, relative cost (0..1), what we hope happens
ACTION_INFO = {
    RETRY_COMM: ("Retry communication in current mode", 0.05, "Link re-established if Earth is now listening in this mode."),
    SWITCH_BACKUP: ("Switch to backup communication mode", 0.25, "Improved chance of restoring communication."),
    SWITCH_LOW_RATE: ("Switch to low-rate robust mode", 0.25, "Slow but more robust link."),
    SWITCH_PRIMARY: ("Switch back to primary mode", 0.20, "Higher data rate for backlog transfer."),
    ADJUST_SIGNAL: ("Adjust simulated signal settings", 0.15, "Slightly stronger signal / better antenna pointing."),
    RESTART_SERVICE: ("Restart simulated communication service", 0.40, "Radio service comes back online."),
    WAIT_WINDOW: ("Wait for a better communication window", 0.02, "Link returns when the blockage/interference passes."),
    REDUCE_LOAD: ("Reduce non-essential probe activity", 0.20, "More power available to the transmitter."),
    STORE_DATA: ("Protect mission data in on-board storage", 0.05, "No mission data is overwritten during the outage."),
    MONITOR: ("Continue monitoring", 0.01, "Keep watching all subsystems."),
    REPORT_STATUS: ("Report status to Earth", 0.05, "Earth learns the cause and the action taken."),
}

MODE_FOR_SWITCH = {SWITCH_BACKUP: BACKUP, SWITCH_LOW_RATE: LOW_RATE, SWITCH_PRIMARY: PRIMARY}


def label(action):
    return ACTION_INFO[action][0]


def apply_action(action, probe, env, rng, tick):
    """Apply one action to the probe. Returns (ok, note). ok=False means it visibly failed."""
    if action in MODE_FOR_SWITCH:
        probe.mode = MODE_FOR_SWITCH[action]
        probe.mode_changed_tick = tick
        probe.energy_used += 0.5
        return True, f"Probe mode is now {probe.mode}"
    if action == RESTART_SERVICE:
        ok = probe.restart_comm_service(rng, env)
        return ok, "Communication service restarted" if ok else "Restart did not complete"
    if action == ADJUST_SIGNAL:
        probe.adjust_signal_settings()
        probe.energy_used += 0.3
        return True, f"Signal trim now x{probe.gain_trim:.2f}"
    if action == REDUCE_LOAD:
        probe.reduce_nonessential()
        return True, "Non-essential loads switched off (POWER_SAVE)"
    if action == STORE_DATA:
        probe.storage.protect()
        return True, f"Protected mission storage enabled ({probe.storage.capacity} packets)"
    return True, ACTION_INFO[action][0]
