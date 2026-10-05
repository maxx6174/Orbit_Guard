# Architecture

All parts run in one Python process. `Engine.step()` advances everything by one tick (1 simulated second).

| Module | File | Job |
|---|---|---|
| Engine | `app/simulation/engine.py` | Order of events each tick, metrics, history |
| Environment | `app/simulation/environment.py` | Communication window, obstruction, interference |
| Faults | `app/simulation/faults.py` | The 6 injectable faults and how they expire |
| Channel | `app/communication/channel.py` | Signal → decodable? → packet delivery probability; mode must match |
| Modes | `app/communication/modes.py` | PRIMARY / BACKUP / LOW_RATE (gain, decode limit, bandwidth) |
| Probe | `app/probe/probe.py`, `storage.py` | Battery, antenna, service, modes, on-board data store |
| Earth | `app/earth/station.py` | Silence detection + cycling recovery strategies |
| Agent | `app/agent/` | ORBIT-GUARD (see HOW_IT_WORKS.md) |
| Mission data | `app/mission/` | SIMULATED PLANETARY DATA packets |
| UI | `app/dashboard.py`, `app/utils/render.py` | Streamlit page + HTML/SVG builders |

## Tick order
1. Environment update, expire faults, probe physics (battery, temperature)
2. Probe generates a data packet and stores it (always)
3. Channel is evaluated; if contact, probe sends up to `bandwidth` packets; each is delivered with probability `delivery`
4. Ground-truth health + metrics bookkeeping
5. Earth reacts (`EarthStation.step`)
6. ORBIT-GUARD observes (only probe-visible readings) and acts

## Key rule: both sides must be on the same mode
Earth cannot see or change the probe's mode. In Earth-only runs the probe stays on PRIMARY, so if PRIMARY is broken
Earth can only wait. With ORBIT-GUARD the probe moves to a working mode and Earth's mode sweep finds it
(or the change is coordinated over a still-working weak link).
