"""Data containers shared by the ORBIT-GUARD agent modules."""
from dataclasses import dataclass, field


@dataclass
class Observation:
    """Everything the probe-side agent is allowed to know on one tick."""
    tick: int
    comm_status: str            # CONNECTED / WEAK / DELAYED / LOST (as the probe sees it)
    ack: bool                   # did Earth answer on this tick?
    silent_ticks: int           # ticks since Earth was last heard
    link_quality: float         # smoothed packet-ack rate (0..1)
    signal: float               # measured signal in the current mode
    mode_scan: dict             # self-test: signal the probe could get in each mode
    path_quality: float         # estimated external attenuation (1 = clear, 0 = blocked)
    battery: float
    antenna_status: str
    antenna_health: float
    transmitter: str
    receiver: str
    service_up: bool
    primary_ok: bool
    temperature: float
    operating_mode: str
    comm_mode: str
    failed_attempts: int
    backlog: int                # packets waiting in storage
    nonessential_on: bool
    gain_trim: float
    battery_effective: float = 0.0
    available_actions: list = field(default_factory=list)


@dataclass
class Decision:
    action: str
    label: str
    reason: str
    priority: int               # 1 = highest
    confidence: float           # 0..1 (estimated chance the action helps)
    expected_result: str
    utility: float = 0.0
    alternatives: list = field(default_factory=list)   # [(label, confidence), ...]
    llm_note: str = ""
