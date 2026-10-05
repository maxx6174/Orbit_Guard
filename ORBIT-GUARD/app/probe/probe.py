"""The simulated planetary probe (state only; decisions live in app/agent)."""
import math

from app.communication.modes import PRIMARY
from app.probe.storage import DataStorage


class Probe:
    def __init__(self):
        self.battery = 85.0            # percent
        self.temperature = -58.0       # simulated degrees C
        self.mode = PRIMARY            # current communication mode
        self.mode_changed_tick = 0
        self.comm_service_up = True
        self.antenna_health = 1.0      # 1.0 = perfect, 0.0 = dead
        self.gain_trim = 1.0           # small signal boost from "adjust settings"
        self.primary_failed = False
        self.power_fault = False
        self.nonessential_on = True    # science extras / heaters etc.
        self.operating_mode = "NORMAL"
        self.storage = DataStorage()
        self.energy_used = 0.0         # abstract communication energy units
        self.last_ack_tick = 0         # last time Earth was heard
        self.angle = 0.0               # orbit angle just for the picture

    # ---- derived status shown on the dashboard ----
    @property
    def battery_effective(self):
        """Battery as seen by the radio. Shedding non-essential load frees headroom."""
        return self.battery + (0 if self.nonessential_on else 12)

    def tx_factor(self):
        return max(0.05, min(1.0, self.battery_effective / 40.0))

    @property
    def transmitter_status(self):
        if not self.comm_service_up:
            return "OFFLINE"
        return "LOW POWER" if self.tx_factor() < 0.6 else "OK"

    @property
    def receiver_status(self):
        return "OK" if self.comm_service_up else "OFFLINE"

    @property
    def antenna_status(self):
        if self.antenna_health > 0.8:
            return "OK"
        return "DEGRADED" if self.antenna_health > 0.4 else "FAILED"

    @property
    def primary_selftest_ok(self):
        return not self.primary_failed

    # ---- per-tick physics ----
    def step(self, tick, rng):
        drain = 0.15 if self.nonessential_on else 0.05
        solar = 0.02 if self.power_fault else 0.20
        self.battery = max(1.0, min(100.0, self.battery + solar - drain))
        self.temperature = round(-58 + 4 * math.sin(tick / 30) + rng.uniform(-0.4, 0.4), 2)
        self.angle = (tick * 4) % 360

    # ---- actions the agent may take ----
    def restart_comm_service(self, rng, env):
        """Simulated restart. Works 80% of the time."""
        self.energy_used += 2.0
        if rng.random() < 0.8:
            self.comm_service_up = True
            env.active.pop("LOSE_COMMUNICATION", None)
            return True
        return False

    def adjust_signal_settings(self):
        self.gain_trim = min(1.24, self.gain_trim + 0.08)
        if self.antenna_health < 1.0:
            self.antenna_health = min(0.5, self.antenna_health + 0.10)

    def reduce_nonessential(self):
        self.nonessential_on = False
        self.operating_mode = "POWER_SAVE"
