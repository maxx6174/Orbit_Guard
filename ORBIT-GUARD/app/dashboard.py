"""ORBIT-GUARD dashboard.  Run with:  streamlit run app/dashboard.py"""
import os
import sys

# make "import app...." work no matter where Streamlit is started from
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
import streamlit.components.v1 as components  # noqa: E402

from app.simulation import faults as F  # noqa: E402
from app.simulation.demo import DEMO_FAULT_TICK, advance, milestones  # noqa: E402
from app.simulation.engine import EARTH_AGENT, EARTH_ONLY, MODE_LABELS, Engine  # noqa: E402
from app.utils import render  # noqa: E402
from app.utils.compare import all_faults_matrix, comparison_table, run_pair  # noqa: E402

st.set_page_config(page_title="ORBIT-GUARD", page_icon="🛰️", layout="wide")
st.markdown(render.CSS, unsafe_allow_html=True)

FAULT_BUTTONS = [(F.LOSE_COMMUNICATION, "📡 LOSE COMMUNICATION"), (F.WEAK_SIGNAL, "📉 WEAK SIGNAL"),
                 (F.ANTENNA_FAILURE, "🛠️ ANTENNA FAILURE"), (F.POWER_DROP, "🔋 POWER DROP"),
                 (F.PRIMARY_MODE_FAILURE, "⛔ PRIMARY MODE FAILURE"), (F.PLANETARY_OBSTRUCTION, "🪐 PLANETARY OBSTRUCTION")]


# ------------------------------------------------------------------ session state
def new_mission(mode=None, running=False, demo=False):
    mode = mode or st.session_state.get("mode", EARTH_AGENT)
    st.session_state.mode = mode
    st.session_state.engine = Engine(mode, seed=st.session_state.get("seed", 7))
    st.session_state.running = running
    st.session_state.demo = demo


if "engine" not in st.session_state:
    st.session_state.results = {}
    new_mission(EARTH_AGENT)

# ------------------------------------------------------------------ header
st.markdown('<p class="og-title">🛰️ ORBIT-GUARD</p>'
            '<p class="og-sub">AI Agent for Two-Way Communication Recovery in Planetary Missions</p>'
            '<span class="og-banner">⚠ SOFTWARE PROTOTYPE / SIMULATION - all data is SIMULATED PLANETARY DATA. '
            'Not tested in space; recovery is never guaranteed.</span>', unsafe_allow_html=True)

tab_live, tab_cmp, tab_about = st.tabs(["🛰️ Live Mission", "📊 Comparison", "ℹ️ About"])

# ================================================================== LIVE TAB
with tab_live:
    c1, c2, c3, c4, c5 = st.columns([1.6, 1, 1, 1, 1.4])
    with c1:
        choice = st.radio("Demo mode", [EARTH_AGENT, EARTH_ONLY], format_func=MODE_LABELS.get, horizontal=True,
                          index=0 if st.session_state.mode == EARTH_AGENT else 1, key="mode_radio")
        if choice != st.session_state.mode:
            new_mission(choice)
            st.rerun()
    with c2:
        if st.button("▶ START DEMO", type="primary", use_container_width=True):
            new_mission(running=True, demo=True)
            st.rerun()
    with c3:
        label = "⏸ PAUSE" if st.session_state.running else "▶ RESUME"
        if st.button(label, use_container_width=True):
            st.session_state.running = not st.session_state.running
            st.rerun()
    with c4:
        if st.button("↺ RESET MISSION", use_container_width=True):
            new_mission(running=False, demo=False)
            st.rerun()
    with c5:
        pace = st.select_slider("Pace", ["Slow", "Normal", "Fast"], value="Normal")
    speed = 1
    refresh = {"Slow": 1.4, "Normal": 0.7, "Fast": 0.3}.get(pace, 0.7)

    st.markdown("**Fault injection panel**")
    fcols = st.columns(len(FAULT_BUTTONS))
    for col, (fid, text) in zip(fcols, FAULT_BUTTONS):
        if col.button(text, key=f"f_{fid}", use_container_width=True):
            st.session_state.engine.inject_fault(fid)
            st.session_state.running = True
            st.rerun()

    def live_view():
        eng = st.session_state.engine
        if st.session_state.running:
            for _ in range(speed):
                if st.session_state.demo:
                    advance(eng)
                else:
                    eng.step()
            if st.session_state.demo and eng.finished():
                st.session_state.running = False
                eng.log.add(eng.tick, "MISSION", "DEMO COMPLETE - mission back to normal", "good")
                st.rerun()

        left, mid, right = st.columns([1, 1.25, 1.1])
        with left:
            st.markdown(render.earth_card(eng), unsafe_allow_html=True)
            if st.session_state.demo or eng.fault_tick is not None:
                st.markdown(render.demo_steps_html(milestones(eng)), unsafe_allow_html=True)
        with mid:
            components.html(render.link_svg(eng), height=235)
            st.markdown(render.stage_tracker(eng), unsafe_allow_html=True)
            hist = pd.DataFrame(eng.history[-80:])
            if not hist.empty:
                st.caption("Signal strength and packet delivery (simulated)")
                st.line_chart(hist.set_index("tick")[["signal", "delivery"]], height=150)
                st.caption("Packets stored on the probe (backlog) - grows during an outage, drains after recovery")
                st.area_chart(hist.set_index("tick")[["backlog"]], height=120)
        with right:
            st.markdown(render.probe_card(eng), unsafe_allow_html=True)

        # mission data graph + latest packet
        gcol, tcol = st.columns([1.6, 1])
        with gcol:
            st.caption("SIMULATED PLANETARY DATA - temperature received on Earth (stored data shown separately)")
            pk = sorted(eng.earth.received.values(), key=lambda p: p.seq)[-150:]
            if pk:
                df = pd.DataFrame({"seq": [p.seq for p in pk],
                                   "Live data": [None if p.during_outage else p.data["temperature_c"] for p in pk],
                                   "Stored data recovered": [p.data["temperature_c"] if p.during_outage else None for p in pk]})
                st.line_chart(df.set_index("seq"), height=170)
        with tcol:
            if eng.earth.last_data:
                st.caption("Latest packet received by Earth")
                st.dataframe(pd.Series(eng.earth.last_data, name="value").astype(str), height=190)

        st.markdown("**Event log**")
        st.markdown(render.event_log_html(eng.log), unsafe_allow_html=True)
        st.caption(f"Simulation tick {eng.tick} (1 tick = 1 simulated second; use Pace = Slow when presenting) | demo injects its fault at tick {DEMO_FAULT_TICK}")

    st.fragment(run_every=refresh if st.session_state.running else None)(live_view)()

# ================================================================== COMPARISON TAB
with tab_cmp:
    st.subheader("Earth Only vs Earth + ORBIT-GUARD")
    st.write("Each button runs a full headless simulation with the same fault and the same random seed. "
             "Every number below is measured from the simulation - nothing is typed in by hand.")
    k1, k2, k3 = st.columns([2, 1, 1])
    fault = k1.selectbox("Fault to test", list(F.FAULTS), format_func=lambda f: F.FAULTS[f].label,
                         index=list(F.FAULTS).index(F.ANTENNA_FAILURE))
    seed = k2.number_input("Random seed", 1, 9999, 7)
    st.session_state.seed = int(seed)
    b1, b2, b3 = st.columns(3)
    from app.simulation.engine import run_scenario  # noqa: E402
    if b1.button("▶ RUN EARTH ONLY", use_container_width=True):
        st.session_state.results["earth"] = run_scenario(fault, EARTH_ONLY, int(seed)).metrics()
    if b2.button("▶ RUN EARTH + ORBIT-GUARD", use_container_width=True):
        st.session_state.results["guard"] = run_scenario(fault, EARTH_AGENT, int(seed)).metrics()
    if b3.button("▶ RUN BOTH", use_container_width=True, type="primary"):
        e, g = run_pair(fault, int(seed))
        st.session_state.results.update(earth=e, guard=g)
    res = st.session_state.results
    if "earth" in res and "guard" in res:
        st.dataframe(comparison_table(res["earth"], res["guard"]), use_container_width=True, hide_index=True)
        if res["earth"].fault != res["guard"].fault:
            st.warning("The two results were run with different faults - run both again for a fair comparison.")
    else:
        st.info("Run both tests to see the comparison table.")
    st.markdown("---")
    st.markdown("**All six faults (reality check)** - some faults, like a planetary obstruction, cannot be sped up by any software.")
    if st.button("Run all faults"):
        st.session_state.matrix = all_faults_matrix(int(seed))
    if "matrix" in st.session_state:
        st.dataframe(st.session_state.matrix, use_container_width=True, hide_index=True)
    st.caption("Assumption: a plain probe keeps only a 40-packet FIFO buffer; ORBIT-GUARD reserves a 400-packet "
               "protected store when an outage starts (see app/simulation/config.py).")

# ================================================================== ABOUT TAB
with tab_about:
    st.markdown("""
**What is this?** A *software simulation* of a planetary probe and an Earth station. When the link drops,
**both sides** try to fix it: Earth cycles through recovery strategies, and the probe's onboard agent **ORBIT-GUARD**
runs *check → diagnose → choose action → try → verify*.

**What this is not:** it is not connected to real hardware, has not been tested in space, and cannot guarantee
communication recovery. All planetary readings are labelled **SIMULATED PLANETARY DATA**.

**How the AI works (no internet, no paid API):** a local decision system that (1) scores likely causes from probe
readings, (2) scores each recovery action using a cause→action table blended with a live self-test of every
communication mode, and (3) learns during the mission which actions fail. An optional local LLM (Ollama) can
phrase the explanation but never changes the decision. See `docs/HOW_IT_WORKS.md`.
""")
