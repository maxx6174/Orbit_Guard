"""The simulated Earth <-> probe radio channel."""
import math
from dataclasses import dataclass

from app.communication.modes import BACKUP, LOW_RATE, MODE_SPECS
from app.simulation.config import ONE_WAY_DELAY_S

CONNECTED, WEAK, DELAYED, LOST = "CONNECTED", "WEAK", "DELAYED", "LOST"


@dataclass
class LinkReport:
    state: str = CONNECTED
    contact: bool = True       # can the two sides exchange data right now?
    signal: float = 0.95       # signal level the probe measures in its own mode
    delivery: float = 0.97     # chance that one packet gets through
    mode_match: bool = True
    delay_s: float = ONE_WAY_DELAY_S
    reason: str = "Nominal"


def physical_signal(probe, mode, env, earth_boost=1.0):
    """Signal level (0..1) the probe would have in `mode`."""
    if not probe.comm_service_up:
        return 0.0
    spec = MODE_SPECS[mode]
    gain = spec.gain
    if mode == "PRIMARY" and probe.primary_failed:
        gain = 0.0
    antenna = probe.antenna_health
    if mode == BACKUP:       # separate small antenna is less affected
        antenna = max(antenna, 0.55)
    if mode == LOW_RATE:
        antenna = max(antenna, 0.35)
    signal = (gain * antenna * probe.tx_factor() * probe.gain_trim
              * env.path_factor() * (0.85 + 0.15 * earth_boost))
    return max(0.0, min(1.0, signal))


def delivery_for(signal, mode):
    """Chance (0..0.98) that one packet gets through at this signal level."""
    spec = MODE_SPECS[mode]
    if signal < spec.min_signal:
        return 0.0
    q = signal / spec.min_signal
    return max(0.0, min(0.98, 1 - math.exp(-(q - 1) * 0.9)))


class Channel:
    def __init__(self, rng):
        self.rng = rng

    def evaluate(self, probe, earth_mode, earth_boost, env):
        noise = 1.0 + self.rng.uniform(-0.03, 0.03)
        signal = physical_signal(probe, probe.mode, env, earth_boost) * noise
        spec = MODE_SPECS[probe.mode]
        mode_match = probe.mode == earth_mode
        decodable = signal >= spec.min_signal
        contact = mode_match and decodable and probe.comm_service_up
        # delivery rises as the signal gets further above the decode limit
        delivery = delivery_for(signal, probe.mode)
        delay = ONE_WAY_DELAY_S + (8 if probe.mode == LOW_RATE else 0)

        if not probe.comm_service_up:
            reason = "Probe communication service is not responding"
        elif not decodable:
            reason = "Signal below decode limit"
        elif not mode_match:
            reason = f"Mode mismatch (Earth {earth_mode}, probe {probe.mode})"
        else:
            reason = "Link usable"

        if not contact:
            state, delivery = LOST, 0.0
        elif delivery < 0.7:
            state = WEAK
        elif probe.mode == LOW_RATE:
            state = DELAYED
        else:
            state = CONNECTED
        return LinkReport(state, contact, signal, delivery, mode_match, delay, reason)
