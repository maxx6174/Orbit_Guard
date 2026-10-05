# Demo guide for judges (≈ 4-5 minutes)

**Before you start:** run `run.bat`, open the **Live Mission** tab, set **Demo mode = Earth + ORBIT-GUARD**, Pace = **Slow**,
click **↺ RESET MISSION**. In the Comparison tab, pre-run nothing (you will run it live). Keep the banner
"SOFTWARE PROTOTYPE / SIMULATION" visible.

| Time | What you do | What you say |
|---|---|---|
| 00:00 | Click **▶ RESUME** (not START DEMO). Green link, packets arriving, graphs moving. | "This is a simulated probe sending simulated planetary data to Earth. The link is healthy." |
| 00:30 | Point at Earth panel and the problem. | "In real missions the link can drop - distance, the planet in the way, antenna or power faults. Today only Earth tries to fix it." |
| 01:00 | Click **🛠️ ANTENNA FAILURE**. Link turns red. | "I inject a main-antenna failure. The probe keeps measuring and stores the data." |
| 01:30 | Show Earth panel: *Earth detected connection loss*, attempts counter, strategy cycling. | "Earth detects the loss and cycles retry → backup → low-rate. But Earth cannot see inside the probe." |
| 02:00 | Show right panel: ORBIT-GUARD decision (action, reason, confidence, expected result) and the CHECK→DIAGNOSE→CHOOSE→TRY→VERIFY tracker. | "At the same time the probe's agent checks its antenna and battery, diagnoses a degraded antenna, and picks backup mode." |
| 02:30 | Link turns blue then green. | "Both sides worked at once and the link is restored." |
| 03:00 | Point at backlog graph draining and "Stored data recovered" series in the mission graph. | "The probe sends everything stored during the outage - Earth gets the missing data." |
| 03:30 | Open **Comparison** tab → choose ANTENNA FAILURE → **RUN BOTH**. | "Same fault, same seed. These numbers are measured by the simulation, not typed in." |
| 04:00 | Click **Run all faults**. Point at PLANETARY OBSTRUCTION. | "Two-sided recovery helps most when the fault is on the probe. When the planet blocks the signal, nothing can speed it up - and we show that honestly. Two sides making an effort beats depending on one." |

**Backup plan:** click **▶ START DEMO** for the automatic 11-step story (under a minute), or run `python tools/run_demo_headless.py`.
**Switch to Earth Only** (radio button) and repeat the antenna fault to show Earth waiting for the fault to end by itself.

**Questions to expect**
- *Is this real AI?* A local scoring agent: diagnosis, action utilities, in-mission learning. Optional local LLM for explanations only.
- *Does it guarantee recovery?* No - it is a simulation prototype; see the Limitations in README.
