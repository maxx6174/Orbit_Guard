"""Builds the Earth-only vs Earth+ORBIT-GUARD comparison from real simulation runs."""
import pandas as pd

from app.simulation import faults as F
from app.simulation.engine import EARTH_AGENT, EARTH_ONLY, run_scenario


def _fmt_time(m):
    return f"{m.recovery_ticks} s" if m.recovered else "NOT RECOVERED"


def comparison_table(earth_only, guard):
    rows = [
        ("Recovery time (simulated seconds)", _fmt_time(earth_only), _fmt_time(guard)),
        ("Recovery attempts - total", earth_only.attempts, guard.attempts),
        ("   of which Earth", earth_only.earth_attempts, guard.earth_attempts),
        ("   of which probe (ORBIT-GUARD)", earth_only.probe_attempts, guard.probe_attempts),
        ("Packets generated", earth_only.generated, guard.generated),
        ("Packets successfully delivered", earth_only.delivered, guard.delivered),
        ("Packets lost (overwritten on probe)", earth_only.lost_packets, guard.lost_packets),
        ("Outage packets generated", earth_only.outage_generated, guard.outage_generated),
        ("Stored data recovered", f"{earth_only.outage_recovered} ({earth_only.outage_recovered_pct}%)",
         f"{guard.outage_recovered} ({guard.outage_recovered_pct}%)"),
        ("Probe communication energy (abstract units)", earth_only.energy_used, guard.energy_used),
        ("Recovery success", "YES" if earth_only.recovered else "NO", "YES" if guard.recovered else "NO"),
    ]
    df = pd.DataFrame(rows, columns=["Metric", "Earth Only", "Earth + ORBIT-GUARD"])
    return df.astype({"Earth Only": str, "Earth + ORBIT-GUARD": str})


def run_pair(fault, seed=7):
    return (run_scenario(fault, EARTH_ONLY, seed).metrics(),
            run_scenario(fault, EARTH_AGENT, seed).metrics())


def all_faults_matrix(seed=7):
    rows = []
    for name, info in F.FAULTS.items():
        e, g = run_pair(name, seed)
        rows.append({"Fault": info.label,
                     "Earth Only: recovery (s)": e.recovery_ticks if e.recovered else "none",
                     "Earth + ORBIT-GUARD: recovery (s)": g.recovery_ticks if g.recovered else "none",
                     "Earth Only: data recovered %": e.outage_recovered_pct,
                     "Earth + ORBIT-GUARD: data recovered %": g.outage_recovered_pct})
    return pd.DataFrame(rows)
