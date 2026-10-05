"""The simulation engine: one call to step() advances the whole mission by one tick (~1 second)."""
import random
from dataclasses import dataclass, field

from app.agent import llm_optional  # noqa: F401  (kept so the optional hook is easy to find)
from app.agent.observation import Observation
from app.agent.orbit_guard import OrbitGuard, RECOVERY
from app.communication.channel import LOST, Channel, physical_signal
from app.communication.modes import ALL_MODES, MODE_SPECS
from app.earth.station import EarthStation
from app.mission.generator import MissionDataGenerator
from app.probe.probe import Probe
from app.simulation import faults as F
from app.simulation.config import (FAULT_FREE_WARMUP, GOOD_DELIVERY, HEARTBEAT_TIMEOUT, HORIZON,
                                   RESTORE_STREAK, TX_ENERGY_PER_PACKET)
from app.simulation.environment import Environment
from app.utils.eventlog import EventLog

EARTH_ONLY = "earth_only"
EARTH_AGENT = "earth_orbit_guard"
MODE_LABELS = {EARTH_ONLY: "Earth Only", EARTH_AGENT: "Earth + ORBIT-GUARD"}


@dataclass
class Stats:
    generated: int = 0
    generated_outage: int = 0
    delivered: int = 0
    outage_delivered: int = 0
    dropped: int = 0
    retransmissions: int = 0


@dataclass
class Metrics:
    mode: str
    fault: str
    recovered: bool
    recovery_ticks: object        # int or None
    attempts: int
    earth_attempts: int
    probe_attempts: int
    generated: int
    delivered: int
    lost_packets: int
    outage_generated: int
    outage_recovered: int
    outage_recovered_pct: float
    energy_used: float
    ticks_run: int


class Engine:
    """Holds every part of the simulated mission."""

    def __init__(self, mode=EARTH_AGENT, seed=7):
        self.mode = mode
        self.seed = seed
        self.rng = random.Random(seed)
        self.tick = 0
        self.env = Environment()
        self.probe = Probe()
        self.earth = EarthStation()
        self.channel = Channel(self.rng)
        self.gen = MissionDataGenerator(self.rng)
        self.log = EventLog()
        self.agent = OrbitGuard() if mode == EARTH_AGENT else None
        self.stats = Stats()
        self.link = self.channel.evaluate(self.probe, self.earth.mode, self.earth.boost, self.env)
        self.link_quality = 1.0              # smoothed ack rate seen by the probe
        self.unhealthy = False               # ground truth, used to label outage packets
        self.healthy_streak = 0
        self.down_since = None               # tick at which the link first became unhealthy
        self.restored_at = None
        self.fault_tick = None
        self.fault_name = None
        self.transfer_started = False
        self.transfer_done = False
        self.history = []                    # per-tick rows for charts
        self.log.add(0, "MISSION", f"Mission started ({MODE_LABELS[mode]}) - SIMULATED PLANETARY DATA", "info")

    # ------------------------------------------------------------------ faults
    def inject_fault(self, name):
        F.inject(name, self.probe, self.env, self.tick)
        if self.fault_tick is None:
            self.fault_tick, self.fault_name = self.tick, name
        self.log.add(self.tick, "FAULT", f"FAULT INJECTED: {F.FAULTS[name].label} - {F.FAULTS[name].description}", "bad")

    # ------------------------------------------------- hooks the agent can use
    def report_status(self, tick, cause, action):
        self.earth.last_message = f"Probe status report: cause '{cause}', action '{action}'"
        self.log.add(tick, "PROBE", "Status report sent to Earth", "info")

    def coordinate_mode(self, mode):
        self.earth.mode = mode

    @property
    def backlog(self):
        return len(self.probe.storage)

    # -------------------------------------------------------------------- tick
    def step(self):
        self.tick += 1
        t = self.tick
        probe, earth, log, stats = self.probe, self.earth, self.log, self.stats

        self.env.update(t)
        for name in F.expire(probe, self.env, t):
            log.add(t, "FAULT", f"{F.FAULTS[name].label} cleared (simulated natural end of condition)", "info")
        probe.step(t, self.rng)

        # 1. the probe keeps generating and storing data no matter what
        pkt = self.gen.next(t, during_outage=self.unhealthy)
        if probe.storage.add(pkt) is not None:
            stats.dropped += 1
            if stats.dropped == 1:
                log.add(t, "PROBE", "Storage full - oldest mission data is being overwritten", "bad")
        stats.generated += 1
        stats.generated_outage += 1 if pkt.during_outage else 0

        # 2. radio link for this tick
        link = self.channel.evaluate(probe, earth.mode, earth.boost, self.env)
        self.link = link
        delivered_n = attempted = 0
        if link.contact:
            probe.last_ack_tick = t
            batch = probe.storage.peek(MODE_SPECS[probe.mode].bandwidth)
            sent = []
            for p in batch:
                attempted += 1
                probe.energy_used += TX_ENERGY_PER_PACKET
                if self.rng.random() < link.delivery:
                    earth.receive(p, t)
                    sent.append(p)
                    stats.delivered += 1
                    stats.outage_delivered += 1 if p.during_outage else 0
                else:
                    stats.retransmissions += 1
            probe.storage.remove(sent)
            delivered_n = len(sent)
        ratio = (delivered_n / attempted) if attempted else None
        self.link_quality = (0.6 * self.link_quality + 0.4 * ratio) if ratio is not None else self.link_quality * 0.7

        # 3. ground truth health + bookkeeping for metrics and the log
        healthy = link.contact and link.delivery >= GOOD_DELIVERY
        self.healthy_streak = self.healthy_streak + 1 if healthy else 0
        if not healthy and self.down_since is None and self.fault_tick is not None:
            self.down_since = t
            log.add(t, "LINK", f"Communication {link.state}: {link.reason}", "bad")
        if self.down_since is not None and self.restored_at is None and self.healthy_streak >= RESTORE_STREAK:
            self.restored_at = t
            log.add(t, "LINK", f"COMMUNICATION RESTORED after {t - self.down_since} ticks", "good")
        self.unhealthy = not healthy
        if self.restored_at is not None and not self.transfer_started and self.backlog > 5:
            self.transfer_started = True
            log.add(t, "PROBE", f"Stored mission data transfer started ({self.backlog} packets waiting)", "info")
        if self.transfer_started and not self.transfer_done and self.backlog <= 2:
            self.transfer_done = True
            log.add(t, "EARTH", f"Data transfer complete - {stats.outage_delivered} of {stats.generated_outage} "
                                f"outage packets recovered", "good")

        # 4. both sides react
        earth.step(t, link, log)
        if self.agent:
            self.agent.step(self._observe(link), _Ctx(self))
        self._record_history(link)
        if self.restored_at == t and self.fault_tick is not None:
            earth.last_message = "Link restored - receiving stored data"

    # ------------------------------------------------------- probe's own view
    def _observe(self, link):
        p = self.probe
        silent = self.tick - p.last_ack_tick
        scan = {m: physical_signal(p, m, self.env, 1.0) for m in ALL_MODES}
        if silent >= HEARTBEAT_TIMEOUT:
            status = LOST
        else:
            status = link.state
        return Observation(
            tick=self.tick, comm_status=status, ack=link.contact, silent_ticks=silent,
            link_quality=self.link_quality, signal=link.signal, mode_scan=scan,
            path_quality=min(1.0, self.env.path_factor() / 0.94),
            battery=p.battery, antenna_status=p.antenna_status, antenna_health=p.antenna_health,
            transmitter=p.transmitter_status, receiver=p.receiver_status, service_up=p.comm_service_up,
            primary_ok=p.primary_selftest_ok, temperature=p.temperature, operating_mode=p.operating_mode,
            comm_mode=p.mode, failed_attempts=self.agent.failed_attempts if self.agent else 0,
            backlog=self.backlog, nonessential_on=p.nonessential_on, gain_trim=p.gain_trim,
            battery_effective=p.battery_effective)

    def _record_history(self, link):
        e = self.earth
        self.history.append({
            "tick": self.tick, "signal": round(link.signal, 3), "delivery": round(link.delivery, 3),
            "battery": round(self.probe.battery, 1), "backlog": self.backlog,
            "received": len(e.received), "state": link.state})

    # ------------------------------------------------------------ derived info
    @property
    def probe_attempts(self):
        return self.agent.total_attempts if self.agent else 0

    @property
    def missing_packets(self):
        return self.gen.seq - len(self.earth.received)

    @property
    def in_recovery(self):
        return self.earth.in_recovery or (self.agent is not None and self.agent.state == RECOVERY)

    def display_state(self):
        """GREEN/YELLOW/RED/BLUE state for the link picture."""
        if self.link.state == LOST:
            return "RECOVERING" if self.in_recovery else "LOST"
        if self.in_recovery and self.link.state != "CONNECTED":
            return "RECOVERING"
        if self.link.state == "WEAK":
            return "WEAK"
        return "CONNECTED"

    def finished(self):
        """A scenario is finished once the link is back and the backlog has drained."""
        return self.restored_at is not None and (self.transfer_done or self.backlog <= 2) \
            and self.tick > self.restored_at + 2

    def metrics(self):
        s = self.stats
        recovered = self.restored_at is not None
        pct = (100.0 * s.outage_delivered / s.generated_outage) if s.generated_outage else 100.0
        return Metrics(
            mode=self.mode, fault=self.fault_name or "-", recovered=recovered,
            recovery_ticks=(self.restored_at - self.down_since) if recovered and self.down_since else None,
            attempts=self.earth.attempts + self.probe_attempts, earth_attempts=self.earth.attempts,
            probe_attempts=self.probe_attempts, generated=s.generated, delivered=s.delivered,
            lost_packets=s.dropped, outage_generated=s.generated_outage, outage_recovered=s.outage_delivered,
            outage_recovered_pct=round(pct, 1),
            energy_used=round(self.probe.energy_used, 2), ticks_run=self.tick)


class _Ctx:
    """The small set of things the agent is allowed to touch."""

    def __init__(self, engine):
        self.probe, self.env, self.rng, self.log = engine.probe, engine.env, engine.rng, engine.log
        self._engine = engine

    def report_status(self, tick, cause, action):
        self._engine.report_status(tick, cause, action)

    def coordinate_mode(self, mode):
        self._engine.coordinate_mode(mode)


def run_scenario(fault, mode, seed=7, warmup=FAULT_FREE_WARMUP, horizon=HORIZON):
    """Run one headless experiment: warm up, inject `fault`, run until recovered and drained."""
    eng = Engine(mode, seed)
    for _ in range(warmup):
        eng.step()
    eng.inject_fault(fault)
    while eng.tick < horizon and not eng.finished():
        eng.step()
    # let the backlog drain for a few more ticks so "recovered data" is fair
    for _ in range(25):
        if eng.backlog <= 2:
            break
        eng.step()
    return eng
