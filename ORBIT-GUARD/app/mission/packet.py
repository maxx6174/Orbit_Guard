from dataclasses import dataclass, field


@dataclass
class Packet:
    seq: int
    tick: int
    data: dict = field(default_factory=dict)
    during_outage: bool = False   # generated while Earth could not hear the probe
