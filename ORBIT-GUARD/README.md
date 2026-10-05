# 🛰️ ORBIT-GUARD
**AI Agent for Two-Way Communication Recovery in Planetary Missions**

> ⚠️ **SOFTWARE PROTOTYPE / SIMULATION.** Nothing here controls real hardware, has been tested in space, or guarantees
> communication recovery. All planetary readings are labelled **SIMULATED PLANETARY DATA**.

## 1. Problem
A probe sent to another planet can lose contact with Earth (distance, planet blocking the line of sight, antenna or power
problems, communication-system faults, temporary signal problems). Normally only **Earth** keeps trying.

## 2. Our idea
*"If both sides can make an effort, why depend on only one side?"*
The probe carries an onboard AI agent, **ORBIT-GUARD**. When the link drops, Earth tries to reconnect **and** the probe
checks itself, diagnoses the likely cause, and tries its own recovery actions - while safely storing mission data until
the link returns.

## 3. How it works (short)
1. Probe keeps generating simulated science data and stores it locally.
2. Link fails (you inject a fault). Earth and the probe each notice the silence.
3. **Earth** cycles: retry primary → backup mode → low-rate mode → boost uplink → wait for window.
4. **ORBIT-GUARD** enters *Communication Recovery Mode*: `CHECK → DIAGNOSE → CHOOSE → TRY → VERIFY`, repeating until the link is back.
5. Link is restored → the probe transmits stored data → Earth shows the recovered packets.
6. A comparison page runs *Earth Only* vs *Earth + ORBIT-GUARD* on the same fault and seed and shows the **measured** results.

## 4. Architecture
See `docs/ARCHITECTURE.md` and `assets/architecture.svg`.
```
Earth station  <—— simulated channel ——>  Probe  (+ ORBIT-GUARD agent)
        \                |                       /
                  Simulation engine (1 tick = 1 simulated second)
                              |
                  Streamlit dashboard
```

## 5. Features
- Two demo modes: **Earth Only** and **Earth + ORBIT-GUARD**
- Local, offline AI decision system (cause diagnosis + action scoring + in-mission learning). No API key, no internet.
- 6 fault buttons (lose communication, weak signal, antenna failure, power drop, primary mode failure, planetary obstruction)
- Live dashboard: Earth panel, animated colour-coded link (green/yellow/red/blue), probe + agent decision panel, event log, graphs
- One-click **START DEMO** and **RESET MISSION**
- Comparison tables built from real simulation runs (single fault and all six faults)
- Automated tests (`python -m pytest`)
- Optional local LLM explanation via Ollama (off by default)

## 6. Installation (Windows 10/11, Python 3.13)
Easy way: double-click **`setup.bat`**. Manual way (VS Code terminal):
```
cd ORBIT-GUARD
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or use Command Prompt.

## 7. Running
Double-click **`run.bat`**, or:
```
streamlit run app/dashboard.py
```
The browser opens at http://localhost:8501.

## 8. Tests
```
python -m pytest
```

## 9. Demo
Click **▶ START DEMO** (under-a-minute automatic story), or follow `docs/DEMO_GUIDE.md` for the 4-minute judge presentation.
No-dashboard check: `python tools/run_demo_headless.py` and `python tools/compare_cli.py`.

## 10. Folder structure
```
ORBIT-GUARD/
├── README.md  QUICK_START.md  requirements.txt  setup.bat  run.bat  pytest.ini
├── app/
│   ├── dashboard.py            Streamlit UI
│   ├── earth/station.py        Earth recovery logic
│   ├── probe/                  probe state + on-board storage
│   ├── agent/                  ORBIT-GUARD (observation, diagnosis, policy, actions, state machine, optional LLM)
│   ├── communication/          modes + simulated channel
│   ├── simulation/             engine, environment, faults, demo script, config constants
│   ├── mission/                simulated science data + packets
│   └── utils/                  event log, HTML renderers, comparison builder
├── data/sample/  data/logs/    sample mission data, saved logs
├── tests/                      automated tests
├── tools/                      command-line demo + comparison
├── docs/                       ARCHITECTURE, HOW_IT_WORKS, DEMO_GUIDE, TROUBLESHOOTING, PROJECT_EXPLANATION
└── assets/architecture.svg
```

## 11. Limitations (please read)
- Simplified simulation: no orbital physics, no real RF link budget, one probe, one Earth station.
- Time is simulated (1 tick = 1 second); real deep-space delays are minutes to hours.
- ORBIT-GUARD **cannot** speed up physical blockages (e.g. the planet blocking the signal) - the comparison shows this honestly.
- The data-protection benefit depends on an assumption: a plain probe keeps a 40-packet FIFO buffer, ORBIT-GUARD reserves a
  400-packet protected store (`app/simulation/config.py`). Change it and the numbers change.
- Agent knowledge (cause → action table) is hand-written, not trained on real mission data.
- Results vary with the random seed; they illustrate the concept, they do not prove real-world performance.

## 12. Future improvements
Real orbital geometry, link-budget model, multiple probes/relays, trained models on logged data, delay-tolerant networking
(store-and-forward), formal verification of the agent's action safety, richer UI replay of past runs.

### Example output (seed 7, produced by `python tools/compare_cli.py`)
```
ORBIT-GUARD simulation comparison (seed 7) - SOFTWARE SIMULATION, not real space data

                Fault  Earth Only: recovery (s)  Earth + ORBIT-GUARD: recovery (s)  Earth Only: data recovered %  Earth + ORBIT-GUARD: data recovered %
   LOSE COMMUNICATION                        60                                  8                          67.8                                  100.0
          WEAK SIGNAL                        40                                  9                         100.0                                  100.0
      ANTENNA FAILURE                       100                                  9                          40.4                                  100.0
           POWER DROP                        80                                 16                          50.6                                  100.0
 PRIMARY MODE FAILURE                        77                                  9                          52.6                                  100.0
PLANETARY OBSTRUCTION                        37                                 37                         100.0                                  100.0
```
