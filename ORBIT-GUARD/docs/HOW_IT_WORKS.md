# How ORBIT-GUARD works

It is a **local decision system** - no cloud, no API key. It is agent-like because it observes, diagnoses, chooses among
actions, acts, checks the result and adapts.

## The loop
```
NOMINAL MONITORING --(silence >= 3 ticks, or link quality < 50% for 3 ticks)--> COMMUNICATION RECOVERY MODE
   CHECK -> DIAGNOSE -> CHOOSE -> TRY -> VERIFY --healthy 2 ticks--> back to NOMINAL
                 ^                          |
                 +------ not restored ------+
```
On entering recovery it immediately runs **STORE DATA** (protect mission data).

## 1. Observation (`agent/observation.py`)
Comm status, signal strength, battery, antenna/transmitter/receiver status, temperature, operating mode, last contact,
failed attempts, backlog, and a **self-test scan** of the signal it could get in each communication mode.

## 2. Diagnosis (`agent/diagnosis.py`)
Scores 7 possible causes (service down, antenna degraded, power low, primary mode fault, external blockage,
mode mismatch, transient glitch) from the readings and normalises them into probabilities.

## 3. Action scoring (`agent/policy.py`)
For every allowed action:
```
chance = Σ P(cause) × P(action fixes cause)            # editable table EFFECT
if action switches mode: chance = 0.35 × table + 0.65 × (expected packet delivery in that mode from the self-test)
chance = (chance × 3 + past_successes) / (3 + past_tries) # learns during the mission
if it failed in the last 15 ticks: chance × 0.5            # (not for WAIT / RETRY)
utility = chance − 0.15 × cost
```
The best utility wins. The decision carries **reason, priority, confidence, expected result** and the next-best alternatives.

## 4. Actions (`agent/actions.py`)
retry communication · switch to backup / low-rate / primary · adjust signal settings · restart communication service (80% success)
· wait for a better window · reduce non-essential activity · protect/store mission data · continue monitoring · report status to Earth.

## 5. Earth side (`earth/station.py`)
After 3 silent ticks Earth starts recovery and every 4 ticks tries the next step:
retry primary → backup → low-rate → boost uplink power → wait for window → repeat.

## 6. Metrics
Recovery time = first tick the link is unhealthy → first 2 consecutive healthy ticks. Attempts = Earth + probe attempts.
Stored data recovered = packets generated during the outage that Earth finally received. Lost packets = packets the probe
overwrote because its buffer was full. Energy = abstract units for transmissions, restarts and setting changes.

## 7. Optional Ollama (off by default)
```
ollama pull llama3.2
set ORBIT_GUARD_USE_OLLAMA=1
streamlit run app/dashboard.py
```
The model only writes a one-sentence "LLM note" in the decision panel. If Ollama is missing, the note is silently skipped.

## 8. Honest limits
The cause→action table is hand-written; the simulation is simplified; no result here predicts real-world performance.
