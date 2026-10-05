"""On-board mission data storage of the probe."""
from collections import deque

from app.simulation.config import BASELINE_BUFFER, PACKET_KB, PROTECTED_BUFFER


class DataStorage:
    def __init__(self):
        self.capacity = BASELINE_BUFFER   # plain FIFO buffer: oldest data is overwritten
        self.protected = False            # True after ORBIT-GUARD protects mission data
        self.buffer = deque()

    def protect(self):
        """ORBIT-GUARD action: reserve a larger protected store for mission data."""
        self.capacity = PROTECTED_BUFFER
        self.protected = True

    def add(self, packet):
        """Store a packet. Returns the packet that had to be thrown away, if any."""
        dropped = None
        if len(self.buffer) >= self.capacity:
            dropped = self.buffer.popleft()
        self.buffer.append(packet)
        return dropped

    def peek(self, n):
        return list(self.buffer)[:n]

    def remove(self, packets):
        seqs = {p.seq for p in packets}
        self.buffer = deque(p for p in self.buffer if p.seq not in seqs)

    def __len__(self):
        return len(self.buffer)

    def outage_count(self):
        return sum(1 for p in self.buffer if p.during_outage)

    @property
    def size_kb(self):
        return round(len(self.buffer) * PACKET_KB, 1)
