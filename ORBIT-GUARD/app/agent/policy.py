"""Step 3 of the agent loop: score every possible action and pick the best one.

Score = chance the action helps (from a cause->action effectiveness table, blended with a
live self-test of each communication mode, and updated by what worked earlier)
minus a small cost for expensive actions.
"""
from app.agent import actions as A
from app.agent.observation import Decision
from app.agent.diagnosis import (ANTENNA_DEGRADED, EXTERNAL_BLOCKAGE, MODE_MISMATCH, POWER_LOW,
                                 PRIMARY_FAULT, SERVICE_DOWN, TRANSIENT, CAUSE_TEXT, top_causes)
from app.communication.channel import delivery_for
from app.communication.modes import MODE_SPECS

# P(action fixes the problem | cause) - the agent's prior knowledge (editable, see docs)
EFFECT = {
    A.RESTART_SERVICE: {SERVICE_DOWN: 0.85, PRIMARY_FAULT: 0.25, TRANSIENT: 0.30},
    A.SWITCH_BACKUP: {ANTENNA_DEGRADED: 0.80, PRIMARY_FAULT: 0.85, POWER_LOW: 0.20, EXTERNAL_BLOCKAGE: 0.20},
    A.SWITCH_LOW_RATE: {ANTENNA_DEGRADED: 0.60, PRIMARY_FAULT: 0.70, POWER_LOW: 0.50, EXTERNAL_BLOCKAGE: 0.35},
    A.ADJUST_SIGNAL: {EXTERNAL_BLOCKAGE: 0.40, ANTENNA_DEGRADED: 0.35, POWER_LOW: 0.10},
    A.REDUCE_LOAD: {POWER_LOW: 0.85},
    A.WAIT_WINDOW: {EXTERNAL_BLOCKAGE: 0.55, MODE_MISMATCH: 0.60, TRANSIENT: 0.40},
    A.RETRY_COMM: {MODE_MISMATCH: 0.75, TRANSIENT: 0.50, EXTERNAL_BLOCKAGE: 0.20},
    A.MONITOR: {TRANSIENT: 0.15},
}
ORDER = [A.RESTART_SERVICE, A.REDUCE_LOAD, A.SWITCH_BACKUP, A.SWITCH_LOW_RATE,
         A.ADJUST_SIGNAL, A.RETRY_COMM, A.WAIT_WINDOW, A.MONITOR]
NO_PENALTY = {A.WAIT_WINDOW, A.RETRY_COMM, A.MONITOR}
COST_WEIGHT = 0.15
PRIOR_STRENGTH = 3.0      # how many "imaginary" past tries the prior is worth


class ActionScorer:
    def __init__(self):
        self.stats = {}          # action -> [tries, successes]
        self.last_failed = {}    # action -> tick

    def record(self, action, success, tick):
        t = self.stats.setdefault(action, [0, 0])
        t[0] += 1
        t[1] += 1 if success else 0
        if not success:
            self.last_failed[action] = tick

    def candidates(self, obs):
        out = []
        for a in ORDER:
            if a in (A.SWITCH_BACKUP, A.SWITCH_LOW_RATE) and A.MODE_FOR_SWITCH[a] == obs.comm_mode:
                continue
            if a == A.REDUCE_LOAD and not obs.nonessential_on:
                continue
            if a == A.ADJUST_SIGNAL and obs.gain_trim >= 1.24:
                continue
            out.append(a)
        return out

    def _chance(self, action, obs, causes, tick):
        p = sum(causes.get(c, 0.0) * w for c, w in EFFECT.get(action, {}).items())
        if action in A.MODE_FOR_SWITCH:
            mode = A.MODE_FOR_SWITCH[action]
            sig = obs.mode_scan.get(mode, 0.0)
            feas = min(0.92, delivery_for(sig, mode)) if obs.service_up else 0.0
            p = 0.35 * p + 0.65 * feas        # trust the live self-test more than the prior
        tries, wins = self.stats.get(action, [0, 0])
        p = (p * PRIOR_STRENGTH + wins) / (PRIOR_STRENGTH + tries)
        if action not in NO_PENALTY and tick - self.last_failed.get(action, -999) < 15:
            p *= 0.5
        return max(0.0, min(0.99, p))

    def decide(self, obs, causes, tick):
        scored = []
        for a in self.candidates(obs):
            p = self._chance(a, obs, causes, tick)
            scored.append((p - COST_WEIGHT * A.ACTION_INFO[a][1], p, a))
        scored.sort(key=lambda x: -x[0])
        util, p, best = scored[0]
        (c1, _), = top_causes(causes, 1)
        urgent = obs.battery_effective < 15
        priority = 1 if (p >= 0.6 or urgent) else (2 if p >= 0.3 else 3)
        reason = f"Most likely cause: {CAUSE_TEXT[c1]}."
        if obs.failed_attempts:
            reason += f" {obs.failed_attempts} earlier attempt(s) did not restore the link."
        return Decision(best, A.label(best), reason, priority, round(p, 2),
                          A.ACTION_INFO[best][2], round(util, 3),
                          [(A.label(a), round(pp, 2)) for _, pp, a in scored[1:4]])
