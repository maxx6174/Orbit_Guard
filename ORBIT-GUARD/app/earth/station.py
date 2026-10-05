"""Earth control station with its own recovery logic."""
from app.communication.modes import BACKUP, LOW_RATE, PRIMARY
from app.simulation.config import EARTH_ATTEMPT_INTERVAL, HEARTBEAT_TIMEOUT, RESTORE_STREAK

# Earth does not know what is wrong with the probe, so it cycles through these steps.
STRATEGIES = [
    ("RETRY NORMAL COMMUNICATION", PRIMARY, 1.0),
    ("TRY BACKUP MODE", BACKUP, 1.0),
    ("TRY LOW-RATE MODE", LOW_RATE, 1.0),
    ("BOOST UPLINK POWER", PRIMARY, 1.3),
    ("WAIT FOR NEXT WINDOW", PRIMARY, 1.0),
]


class EarthStation:
    def __init__(self):
        self.mode = PRIMARY
        self.boost = 1.0
        self.in_recovery = False
        self.attempts = 0
        self.last_rx_tick = 0
        self.recovery_started = None
        self.next_attempt = 0
        self.strategy_idx = 0
        self.current_strategy = "MONITORING"
        self.stable = 0
        self.received = {}
        self.restored_packets = 0
        self.last_message = "Waiting for first telemetry"
        self.last_data = None

    def receive(self, packet, tick):
        self.received[packet.seq] = packet
        self.last_data = packet.data
        if packet.during_outage:
            self.restored_packets += 1

    def step(self, tick, link, log):
        if link.contact:
            self.last_rx_tick = tick
            self.last_message = f"Telemetry heartbeat received (mode {self.mode})"
        silent = tick - self.last_rx_tick

        if not self.in_recovery:
            if silent >= HEARTBEAT_TIMEOUT:
                self.in_recovery = True
                self.recovery_started = tick
                self.next_attempt = tick
                self.stable = 0
                log.add(tick, "EARTH", "Earth detected connection loss - recovery started", "bad")
            return

        if link.contact:
            self.stable += 1
            if self.stable >= RESTORE_STREAK:
                self.in_recovery = False
                self.current_strategy = "MONITORING"
                self.boost = 1.0
                log.add(tick, "EARTH", f"Earth link re-established on {self.mode} mode", "good")
        else:
            self.stable = 0
            if tick >= self.next_attempt:
                self._attempt(tick, log)

    def _attempt(self, tick, log):
        name, mode, boost = STRATEGIES[self.strategy_idx % len(STRATEGIES)]
        self.strategy_idx += 1
        self.attempts += 1
        self.mode, self.boost = mode, boost
        self.current_strategy = name
        self.next_attempt = tick + EARTH_ATTEMPT_INTERVAL
        log.add(tick, "EARTH", f"Earth attempt #{self.attempts}: {name}", "info")

    @property
    def missing_packets(self):
        return None  # computed by the engine, which knows how many were generated
