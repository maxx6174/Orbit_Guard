"""Generates SIMULATED PLANETARY DATA. Nothing here is a real measurement."""
import math

from app.mission.packet import Packet

LABEL = "SIMULATED PLANETARY DATA"


class MissionDataGenerator:
    def __init__(self, rng):
        self.rng = rng
        self.seq = 0

    def next(self, tick, during_outage=False):
        r = self.rng
        self.seq += 1
        data = {
            "temperature_c": round(-60 + 8 * math.sin(tick / 25) + r.uniform(-1.5, 1.5), 2),
            "pressure_pa": round(610 + 15 * math.sin(tick / 40) + r.uniform(-4, 4), 1),
            "atmosphere_co2_pct": round(95.3 + r.uniform(-0.4, 0.4), 2),
            "radiation_usv_h": round(0.65 + 0.15 * math.sin(tick / 15) + r.uniform(-0.03, 0.03), 3),
            "soil_ph": round(7.7 + r.uniform(-0.15, 0.15), 2),
            "gas_methane_ppb": round(max(0.0, 12 + 6 * math.sin(tick / 30) + r.uniform(-2, 2)), 2),
            "water_index": round(max(0.0, min(1.0, 0.2 + 0.1 * math.sin(tick / 35) + r.uniform(-0.03, 0.03))), 3),
            "latitude": round(18.4 + 0.02 * tick, 3),
            "longitude": round(77.5 + 0.015 * tick, 3),
            "label": LABEL,
        }
        return Packet(self.seq, tick, data, during_outage)
