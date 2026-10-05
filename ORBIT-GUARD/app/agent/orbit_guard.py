"""ORBIT-GUARD: the probe-side recovery agent.

Core loop (runs once per simulation tick):

    NOMINAL --(loss detected)--> RECOVERY MODE
    CHECK -> DIAGNOSE -> CHOOSE -> TRY -> VERIFY --success--> NOMINAL
                 ^                           |
                 +-------- failure ----------+
"""
from app.agent import actions as A
from app.agent import llm_optional
from app.agent.diagnosis import CAUSE_TEXT, diagnose, top_causes
from app.agent.observation import Decision
from app.agent.policy import ActionScorer
from app.communication.channel import delivery_for
from app.communication.modes import ALL_MODES, MODE_SPECS
from app.simulation.config import GOOD_DELIVERY, HEARTBEAT_TIMEOUT, RESTORE_STREAK

NOMINAL, RECOVERY = "NOMINAL MONITORING", "COMMUNICATION RECOVERY MODE"
CHECK, DIAGNOSE, CHOOSE, TRY, VERIFY, IDLE = "CHECK", "DIAGNOSE", "CHOOSE", "TRY", "VERIFY", "-"
VERIFY_TICKS = 8
MODE_VERIFY_TICKS = 22     # Earth sweeps modes slowly, so a mode switch needs longer to judge


class OrbitGuard:
    def __init__(self):
        self.state = NOMINAL
        self.phase = IDLE
        self.scorer = ActionScorer()
        self.decision = None
        self.causes = {}
        self.failed_attempts = 0
        self.total_attempts = 0
        self.recovery_started = None
        self.phase_tick = 0
        self.verify_left = 0
        self.low_quality_ticks = 0
        self.healthy_streak = 0
        self.last_action_note = ""
        self.attempt_history = []      # for the dashboard / report
        self.first_pass = True
        self.last_root_cause = ""

    # ------------------------------------------------------------------ public
    def step(self, obs, ctx):
        """ctx gives the agent access to the probe, log, rng, env and Earth coordination."""
        self._track(obs)
        if self.state == NOMINAL:
            if self._loss_detected(obs):
                self._enter_recovery(obs, ctx)
            else:
                self._housekeeping(obs, ctx)
            return
        self._recovery_step(obs, ctx)

    # ----------------------------------------------------------------- tracking
    def _track(self, obs):
        healthy = obs.ack and obs.link_quality >= GOOD_DELIVERY - 0.05
        self.healthy_streak = self.healthy_streak + 1 if healthy else 0
        self.low_quality_ticks = self.low_quality_ticks + 1 if (obs.ack and obs.link_quality < 0.5) else 0

    def _loss_detected(self, obs):
        return obs.silent_ticks >= HEARTBEAT_TIMEOUT or self.low_quality_ticks >= 3

    # ----------------------------------------------------------- entering / exit
    def _enter_recovery(self, obs, ctx):
        self.state, self.phase = RECOVERY, CHECK
        self.recovery_started = obs.tick
        self.failed_attempts = 0
        self.first_pass = True
        self.healthy_streak = 0
        kind = "communication loss" if obs.silent_ticks >= HEARTBEAT_TIMEOUT else "severely degraded link"
        ctx.log.add(obs.tick, "ORBIT-GUARD", f"ORBIT-GUARD detected {kind}", "bad")
        ctx.log.add(obs.tick, "ORBIT-GUARD", "Entering COMMUNICATION RECOVERY MODE", "warn")
        ok, note = A.apply_action(A.STORE_DATA, ctx.probe, ctx.env, ctx.rng, obs.tick)
        ctx.log.add(obs.tick, "ORBIT-GUARD", f"Action STORE DATA: {note}", "info")
        self.decision = Decision(A.STORE_DATA, A.label(A.STORE_DATA), "Link is down; protect science data first.",
                                 1, 0.95, A.ACTION_INFO[A.STORE_DATA][2])

    def _succeed(self, obs, ctx):
        dur = obs.tick - self.recovery_started
        if self.decision and self.decision.action not in (A.STORE_DATA,):
            self.scorer.record(self.decision.action, True, obs.tick)
        ctx.log.add(obs.tick, "ORBIT-GUARD", f"Communication restored after {dur} ticks - returning to normal mode", "good")
        self.attempt_history.append((obs.tick, self.decision.label if self.decision else "-", "SUCCESS"))
        self.state, self.phase = NOMINAL, IDLE
        ctx.report_status(obs.tick, self.last_root_cause, self.decision.label if self.decision else "-")
        self.verify_left = 0

    # ----------------------------------------------------------------- recovery
    def _recovery_step(self, obs, ctx):
        if self.phase == VERIFY:
            if self.healthy_streak >= RESTORE_STREAK:
                return self._succeed(obs, ctx)
            self.verify_left -= 1
            if self.verify_left <= 0:
                self._fail(obs, ctx, "no response")
            return
        if self.phase == CHECK:
            ctx.log.add(obs.tick, "PROBE", (f"System check: battery {obs.battery:.0f}%, antenna {obs.antenna_status}, "
                        f"TX {obs.transmitter}, RX {obs.receiver}, mode {obs.comm_mode}"), "info")
            self.phase = DIAGNOSE
            if self.first_pass:
                return
        if self.phase == DIAGNOSE:
            self.causes = diagnose(obs)
            top = [(c, p) for c, p in top_causes(self.causes, 2)]
            top = [top[0]] + [x for x in top[1:] if x[1] >= 0.15]   # only mention a 2nd cause if it matters
            self.last_root_cause = CAUSE_TEXT[top[0][0]]
            ctx.log.add(obs.tick, "ORBIT-GUARD",
                        "Diagnosis: " + "; ".join(f"{CAUSE_TEXT[c]} ({p:.0%})" for c, p in top), "info")
            self.phase = CHOOSE
            if self.first_pass:
                return
        if self.phase == CHOOSE:
            obs.failed_attempts = self.failed_attempts
            self.decision = self.scorer.decide(obs, self.causes, obs.tick)
            d = self.decision
            if llm_optional.enabled():
                d.llm_note = llm_optional.explain(d, self.last_root_cause)
            ctx.log.add(obs.tick, "ORBIT-GUARD",
                        f"Chosen: {d.label} (confidence {d.confidence:.2f}, priority {d.priority})", "info")
            self.phase = TRY
            if self.first_pass:
                return
        if self.phase == TRY:
            self._try(obs, ctx)

    def _try(self, obs, ctx):
        d = self.decision
        self.total_attempts += 1
        ok, note = A.apply_action(d.action, ctx.probe, ctx.env, ctx.rng, obs.tick)
        self.last_action_note = note
        ctx.log.add(obs.tick, "PROBE", f"Probe attempt #{self.total_attempts}: {note}", "info" if ok else "warn")
        if d.action in A.MODE_FOR_SWITCH and obs.ack:
            # the degraded link still works, so the mode change is announced to Earth over it
            ctx.coordinate_mode(ctx.probe.mode)
            ctx.log.add(obs.tick, "PROBE", f"Mode change coordinated with Earth over the weak link ({ctx.probe.mode})", "info")
        self.first_pass = False
        if not ok:                       # visible immediate failure (e.g. restart failed)
            return self._fail(obs, ctx, note)
        self.phase = VERIFY
        self.healthy_streak = 0
        self.verify_left = MODE_VERIFY_TICKS if d.action in A.MODE_FOR_SWITCH else VERIFY_TICKS

    def _fail(self, obs, ctx, why):
        d = self.decision
        self.failed_attempts += 1
        self.scorer.record(d.action, False, obs.tick)
        self.attempt_history.append((obs.tick, d.label, "FAILED"))
        ctx.log.add(obs.tick, "ORBIT-GUARD", f"{d.label}: no recovery yet ({why}) - choosing next action", "warn")
        obs.failed_attempts = self.failed_attempts
        self.causes = diagnose(obs)
        self.phase = CHOOSE
        self._recovery_step(obs, ctx)

    # ------------------------------------------------------------- nominal duties
    def _housekeeping(self, obs, ctx):
        """While healthy: restore normal operations and upgrade the link if there is a backlog."""
        if not obs.nonessential_on and obs.battery >= 45 and obs.ack:
            A.apply_action(A.MONITOR, ctx.probe, ctx.env, ctx.rng, obs.tick)
            ctx.probe.nonessential_on = True
            ctx.probe.operating_mode = "NORMAL"
            ctx.log.add(obs.tick, "ORBIT-GUARD", "Battery recovered - non-essential activity resumed", "info")
        if not (obs.ack and self.healthy_streak >= 3):
            return
        cur = obs.comm_mode
        def throughput(mode):
            sig = obs.mode_scan.get(mode, 0.0)
            return MODE_SPECS[mode].bandwidth * delivery_for(sig, mode)
        usable = [m for m in ALL_MODES if delivery_for(obs.mode_scan.get(m, 0.0), m) >= GOOD_DELIVERY]
        if not usable:
            return
        best = max(usable, key=throughput)
        if best != cur and throughput(best) >= 1.5 * max(throughput(cur), 0.01) and obs.backlog > 2:
            action = {v: k for k, v in A.MODE_FOR_SWITCH.items()}[best]
            ctx.probe.mode = best
            ctx.probe.mode_changed_tick = obs.tick
            ctx.coordinate_mode(best)
            self.decision = Decision(action, A.label(action), "Link is healthy and a faster mode is now usable.", 2,
                                     0.8, A.ACTION_INFO[action][2])
            ctx.log.add(obs.tick, "ORBIT-GUARD", f"Coordinated mode upgrade with Earth -> {best} (faster backlog transfer)", "info")
