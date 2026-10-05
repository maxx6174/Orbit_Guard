"""Central place for simulation constants (all values are SIMULATED)."""

HEARTBEAT_TIMEOUT = 3        # ticks of silence before a side declares "communication lost"
EARTH_ATTEMPT_INTERVAL = 4   # Earth tries a new recovery step every N ticks
MODE_DWELL = 10              # ticks the agent prefers to stay on a mode before switching again
RESTORE_STREAK = 2           # healthy ticks in a row needed to call communication "restored"
GOOD_DELIVERY = 0.70         # delivery probability above this counts as a healthy link

BASELINE_BUFFER = 40         # packets a plain probe can keep (simple FIFO buffer)
PROTECTED_BUFFER = 400       # packets available after ORBIT-GUARD protects mission data
PACKET_KB = 0.5              # pretend size of one packet (for the storage display)

TX_ENERGY_PER_PACKET = 0.05  # abstract "energy units"
ONE_WAY_DELAY_S = 12         # simulated light-time delay shown on the dashboard
FAULT_FREE_WARMUP = 20       # tick at which scenario runs inject their fault
HORIZON = 260                # max ticks for one headless scenario run
