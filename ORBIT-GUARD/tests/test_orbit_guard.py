"""Automated tests for ORBIT-GUARD. Run with:  python -m pytest"""
from app.agent import actions as A
from app.agent.diagnosis import ANTENNA_DEGRADED, POWER_LOW, SERVICE_DOWN, diagnose
from app.agent.orbit_guard import NOMINAL, RECOVERY
from app.agent.policy import ActionScorer
from app.communication.channel import LOST
from app.communication.modes import BACKUP, PRIMARY
from app.simulation import faults as F
from app.simulation.engine import EARTH_AGENT, EARTH_ONLY, Engine, run_scenario


def warm(mode=EARTH_AGENT, ticks=20, seed=7):
    eng = Engine(mode, seed)
    for _ in range(ticks):
        eng.step()
    return eng


def run_until(eng, cond, limit=300):
    while not cond(eng) and eng.tick < limit:
        eng.step()
    return eng


# ---------------------------------------------------------------- normal operation
def test_normal_communication_delivers_data():
    eng = warm()
    assert eng.link.contact and eng.display_state() == "CONNECTED"
    assert len(eng.earth.received) >= 15
    assert eng.missing_packets <= 6


# ---------------------------------------------------------------- loss detection
def test_communication_loss_is_detected_by_earth_and_probe():
    eng = warm()
    eng.inject_fault(F.LOSE_COMMUNICATION)
    run_until(eng, lambda e: e.earth.in_recovery and e.agent.state == RECOVERY, 60)
    assert eng.link.state == LOST or eng.earth.in_recovery
    assert eng.earth.in_recovery
    assert eng.agent.state == RECOVERY
    assert eng.log.has("Earth detected connection loss")
    assert eng.log.has("ORBIT-GUARD detected")


def test_earth_only_probe_has_no_agent():
    eng = warm(EARTH_ONLY)
    eng.inject_fault(F.LOSE_COMMUNICATION)
    run_until(eng, lambda e: e.earth.attempts >= 1, 60)
    assert eng.agent is None and eng.probe_attempts == 0
    assert eng.earth.in_recovery


# ---------------------------------------------------------------- Earth recovery
def test_earth_cycles_recovery_strategies():
    eng = warm(EARTH_ONLY)
    eng.inject_fault(F.LOSE_COMMUNICATION)
    run_until(eng, lambda e: e.earth.attempts >= 4, 80)
    names = [e.message for e in eng.log.events if "Earth attempt" in e.message]
    assert any("BACKUP" in n for n in names) and any("LOW-RATE" in n for n in names)


def test_earth_only_recovers_when_fault_clears():
    eng = run_scenario(F.PLANETARY_OBSTRUCTION, EARTH_ONLY)
    m = eng.metrics()
    assert m.recovered and m.recovery_ticks >= 25   # Earth must wait for the planet to move


# ---------------------------------------------------------------- probe recovery
def test_probe_recovers_from_antenna_failure_with_backup_mode():
    eng = run_scenario(F.ANTENNA_FAILURE, EARTH_AGENT)
    m = eng.metrics()
    assert m.recovered
    assert m.recovery_ticks < 40            # far earlier than the 100-tick natural fault
    assert eng.log.has("Switch to backup") or eng.log.has("Probe mode is now BACKUP")


def test_probe_recovers_from_service_failure_by_restart():
    eng = run_scenario(F.LOSE_COMMUNICATION, EARTH_AGENT)
    assert eng.metrics().recovered
    assert eng.log.has("restart") or eng.log.has("Restart")


def test_probe_recovers_from_power_drop_by_shedding_load():
    eng = run_scenario(F.POWER_DROP, EARTH_AGENT)
    assert eng.metrics().recovered
    assert eng.log.has("Non-essential loads switched off")


# ---------------------------------------------------------------- agent decisions
def test_agent_picks_backup_mode_when_primary_fails():
    eng = warm()
    eng.inject_fault(F.PRIMARY_MODE_FAILURE)
    run_until(eng, lambda e: e.agent.decision is not None and e.agent.decision.action != A.STORE_DATA, 80)
    d = eng.agent.decision
    assert d.action == A.SWITCH_BACKUP
    assert 0.0 < d.confidence <= 1.0 and d.reason and d.expected_result and d.priority in (1, 2, 3)


def test_agent_picks_restart_when_service_is_down():
    eng = warm()
    eng.inject_fault(F.LOSE_COMMUNICATION)
    run_until(eng, lambda e: e.agent.decision is not None and e.agent.decision.action != A.STORE_DATA, 80)
    assert eng.agent.decision.action == A.RESTART_SERVICE


def test_agent_waits_when_planet_blocks_the_signal():
    eng = warm()
    eng.inject_fault(F.PLANETARY_OBSTRUCTION)
    run_until(eng, lambda e: e.agent.decision is not None and e.agent.decision.action != A.STORE_DATA, 80)
    assert eng.agent.decision.action == A.WAIT_WINDOW


def test_diagnosis_identifies_injected_causes():
    for fault, cause in [(F.LOSE_COMMUNICATION, SERVICE_DOWN), (F.ANTENNA_FAILURE, ANTENNA_DEGRADED),
                         (F.POWER_DROP, POWER_LOW)]:
        eng = warm()
        eng.inject_fault(fault)
        eng.step()
        causes = diagnose(eng._observe(eng.link))
        assert max(causes, key=causes.get) == cause, fault
        assert abs(sum(causes.values()) - 1) < 1e-6


def test_scorer_loses_confidence_in_failing_actions():
    eng = warm()
    eng.inject_fault(F.LOSE_COMMUNICATION)
    eng.step()
    obs = eng._observe(eng.link)
    causes = diagnose(obs)
    scorer = ActionScorer()
    before = scorer.decide(obs, causes, eng.tick)
    for _ in range(3):
        scorer.record(before.action, False, eng.tick)
    after = scorer.decide(obs, causes, eng.tick)
    assert after.confidence < before.confidence * 0.5   # it trusts the failing action much less


# ---------------------------------------------------------------- fault injection
def test_each_fault_changes_the_simulated_condition():
    checks = {
        F.LOSE_COMMUNICATION: lambda e: not e.probe.comm_service_up,
        F.WEAK_SIGNAL: lambda e: e.env.interference < 0.5,
        F.ANTENNA_FAILURE: lambda e: e.probe.antenna_health < 0.3,
        F.POWER_DROP: lambda e: e.probe.battery < 10,
        F.PRIMARY_MODE_FAILURE: lambda e: e.probe.primary_failed,
        F.PLANETARY_OBSTRUCTION: lambda e: e.env.obstruction < 0.2,
    }
    for fault, check in checks.items():
        eng = warm(ticks=5)
        eng.inject_fault(fault)
        assert check(eng), fault
        assert fault in eng.env.active


def test_faults_expire_by_themselves():
    eng = warm(EARTH_ONLY, 5)
    eng.inject_fault(F.WEAK_SIGNAL)
    run_until(eng, lambda e: not e.env.active, 200)
    assert eng.env.interference == 1.0


# ---------------------------------------------------------------- data storage + transfer
def test_data_is_stored_during_outage_and_sent_after_recovery():
    eng = warm()
    eng.inject_fault(F.ANTENNA_FAILURE)
    run_until(eng, lambda e: e.backlog >= 5, 60)
    assert eng.probe.storage.size_kb > 0 and eng.backlog >= 5
    run_until(eng, lambda e: e.finished(), 250)
    assert eng.restored_at is not None
    assert eng.backlog <= 2
    assert eng.stats.outage_delivered > 0
    assert eng.earth.restored_packets == eng.stats.outage_delivered


def test_orbit_guard_protects_data_that_a_plain_probe_loses():
    plain = run_scenario(F.ANTENNA_FAILURE, EARTH_ONLY).metrics()
    guarded = run_scenario(F.ANTENNA_FAILURE, EARTH_AGENT).metrics()
    assert plain.lost_packets > 0            # 40-packet FIFO overflowed
    assert guarded.lost_packets == 0
    assert guarded.outage_recovered_pct >= plain.outage_recovered_pct


# ---------------------------------------------------------------- state changes + comparison
def test_recovery_state_changes_back_to_nominal():
    eng = run_scenario(F.PRIMARY_MODE_FAILURE, EARTH_AGENT)
    assert eng.agent.state == NOMINAL
    assert not eng.earth.in_recovery
    assert eng.display_state() == "CONNECTED"


def test_metrics_are_computed_not_hardcoded():
    a = run_scenario(F.ANTENNA_FAILURE, EARTH_ONLY, seed=1).metrics()
    b = run_scenario(F.ANTENNA_FAILURE, EARTH_ONLY, seed=2).metrics()
    assert a.generated > 0 and a.delivered > 0
    assert (a.energy_used, a.delivered) != (b.energy_used, b.delivered)   # seeds change results


def test_same_seed_is_reproducible():
    a = run_scenario(F.POWER_DROP, EARTH_AGENT, seed=3).metrics()
    b = run_scenario(F.POWER_DROP, EARTH_AGENT, seed=3).metrics()
    assert a == b


def test_orbit_guard_not_slower_on_hardware_faults_across_seeds():
    for fault in (F.LOSE_COMMUNICATION, F.ANTENNA_FAILURE, F.PRIMARY_MODE_FAILURE, F.POWER_DROP):
        for seed in (1, 2, 3, 4, 5):
            e = run_scenario(fault, EARTH_ONLY, seed).metrics()
            g = run_scenario(fault, EARTH_AGENT, seed).metrics()
            assert g.recovered
            assert g.recovery_ticks <= e.recovery_ticks, (fault, seed)


def test_optional_llm_is_off_by_default():
    from app.agent import llm_optional
    assert not llm_optional.enabled()
    assert llm_optional.explain(None, "") == ""
