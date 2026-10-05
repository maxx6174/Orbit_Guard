"""Communication modes. Earth and probe must be on the SAME mode to talk."""
from dataclasses import dataclass

PRIMARY = "PRIMARY"
BACKUP = "BACKUP"
LOW_RATE = "LOW_RATE"
ALL_MODES = (PRIMARY, BACKUP, LOW_RATE)


@dataclass(frozen=True)
class ModeSpec:
    label: str
    gain: float          # how strong the signal is in this mode
    min_signal: float    # weakest signal the mode can still decode
    bandwidth: int       # packets per tick that can be sent


MODE_SPECS = {
    PRIMARY: ModeSpec("Primary high-gain link", 1.00, 0.20, 4),
    BACKUP: ModeSpec("Backup low-gain antenna link", 0.75, 0.15, 2),
    LOW_RATE: ModeSpec("Low-rate robust link", 0.60, 0.07, 1),
}
