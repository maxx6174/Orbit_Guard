"""Pure-Python HTML/SVG builders for the dashboard (kept separate so they can be tested)."""
from app.agent.orbit_guard import CHECK, CHOOSE, DIAGNOSE, TRY, VERIFY
from app.communication.modes import MODE_SPECS

COLORS = {"CONNECTED": "#22c55e", "WEAK": "#eab308", "LOST": "#ef4444", "RECOVERING": "#3b82f6"}
STATE_TEXT = {"CONNECTED": "CONNECTED", "WEAK": "WEAK SIGNAL", "LOST": "COMMUNICATION LOST",
              "RECOVERING": "RECOVERING"}
LOG_COLORS = {"info": "#cbd5e1", "warn": "#facc15", "bad": "#f87171", "good": "#4ade80"}
SRC_COLORS = {"EARTH": "#38bdf8", "PROBE": "#fb923c", "ORBIT-GUARD": "#c084fc",
              "FAULT": "#f87171", "LINK": "#94a3b8", "MISSION": "#94a3b8"}

CSS = """
<style>
.og-title{font-size:2.1rem;font-weight:800;letter-spacing:.12em;margin:0;color:#e2e8f0}
.og-sub{color:#94a3b8;margin:0 0 .4rem 0}
.og-banner{background:#3b2f06;border:1px solid #eab308;color:#fde68a;padding:.3rem .7rem;border-radius:.4rem;
  font-size:.8rem;display:inline-block}
.og-card{background:#111827;border:1px solid #1f2937;border-radius:.7rem;padding:.8rem 1rem;color:#e2e8f0}
.og-card h4{margin:0 0 .5rem 0;font-size:.95rem;letter-spacing:.1em;color:#94a3b8}
.og-row{display:flex;justify-content:space-between;padding:.14rem 0;border-bottom:1px solid #1f2937;font-size:.88rem}
.og-row span:first-child{color:#94a3b8}
.og-pill{padding:.05rem .55rem;border-radius:1rem;font-weight:700;font-size:.8rem;color:#0b1220}
.og-bar{background:#1f2937;border-radius:.4rem;height:.7rem;overflow:hidden}
.og-bar>div{height:100%}
.og-stage{display:inline-block;padding:.15rem .6rem;margin-right:.25rem;border-radius:.4rem;font-size:.78rem;
  background:#1f2937;color:#64748b}
.og-stage.on{background:#7c3aed;color:#fff;font-weight:700}
.og-stage.done{background:#14532d;color:#bbf7d0}
.og-log{background:#0b1220;border:1px solid #1f2937;border-radius:.6rem;padding:.6rem .9rem;
  font-family:Consolas,monospace;font-size:.82rem;max-height:300px;overflow-y:auto}
.og-step{font-size:.85rem;padding:.12rem 0;color:#64748b}
.og-step.ok{color:#4ade80}
</style>
"""


def pill(text, color):
    return f'<span class="og-pill" style="background:{color}">{text}</span>'


def row(label, value):
    return f'<div class="og-row"><span>{label}</span><span>{value}</span></div>'


def status_color(text):
    t = str(text).upper()
    if t in ("OK", "CONNECTED", "NORMAL"):
        return "#22c55e"
    if t in ("DEGRADED", "LOW POWER", "POWER_SAVE", "WEAK", "DELAYED"):
        return "#eab308"
    return "#ef4444"


def bar(frac, color):
    frac = max(0.0, min(1.0, frac))
    return f'<div class="og-bar"><div style="width:{frac*100:.0f}%;background:{color}"></div></div>'


def link_svg(eng):
    """Earth <-> Probe picture with a colour-coded, animated link."""
    state = eng.display_state()
    color = COLORS[state]
    anim = "" if state == "LOST" else \
        f'<line x1="150" y1="100" x2="550" y2="100" stroke="#fff" stroke-width="3" stroke-dasharray="6 26" ' \
        f'opacity=".9"><animate attributeName="stroke-dashoffset" from="64" to="0" dur="{0.8 if state=="CONNECTED" else 1.8}s" repeatCount="indefinite"/></line>'
    cross = '<text x="350" y="92" font-size="30" fill="#ef4444" text-anchor="middle">✕</text>' if state == "LOST" else ""
    pulse = f'<circle cx="350" cy="100" r="18" fill="none" stroke="{color}" stroke-width="2"><animate attributeName="r" from="10" to="34" dur="1.4s" repeatCount="indefinite"/><animate attributeName="opacity" from=".9" to="0" dur="1.4s" repeatCount="indefinite"/></circle>' if state == "RECOVERING" else ""
    spec = MODE_SPECS[eng.probe.mode]
    return f"""
<html><body style="margin:0;background:transparent;font-family:Segoe UI,Arial,sans-serif">
<svg viewBox="0 0 700 215" width="100%" xmlns="http://www.w3.org/2000/svg">
  <defs><radialGradient id="pl"><stop offset="0" stop-color="#60a5fa"/><stop offset="1" stop-color="#1e3a8a"/></radialGradient></defs>
  <line x1="150" y1="100" x2="550" y2="100" stroke="{color}" stroke-width="7" stroke-linecap="round" opacity=".85"/>
  {anim}{pulse}{cross}
  <circle cx="90" cy="100" r="58" fill="url(#pl)" stroke="#93c5fd" stroke-width="2"/>
  <text x="90" y="105" font-size="15" fill="#fff" text-anchor="middle" font-weight="700">EARTH</text>
  <g transform="translate(610,100) rotate({eng.probe.angle*0.0})">
    <rect x="-22" y="-14" width="44" height="28" rx="5" fill="#cbd5e1" stroke="#64748b"/>
    <rect x="-58" y="-9" width="30" height="18" fill="#2563eb"/><rect x="28" y="-9" width="30" height="18" fill="#2563eb"/>
    <circle cx="0" cy="-22" r="8" fill="none" stroke="{'#ef4444' if eng.probe.antenna_status=='FAILED' else '#e2e8f0'}" stroke-width="3"/>
  </g>
  <text x="610" y="160" font-size="15" fill="#e2e8f0" text-anchor="middle" font-weight="700">PROBE</text>
  <text x="350" y="40" font-size="20" fill="{color}" text-anchor="middle" font-weight="800">{STATE_TEXT[state]}</text>
  <text x="350" y="150" font-size="13" fill="#94a3b8" text-anchor="middle">Earth mode: {eng.earth.mode} | Probe mode: {eng.probe.mode} ({spec.label})</text>
  <text x="350" y="172" font-size="13" fill="#94a3b8" text-anchor="middle">signal {eng.link.signal:.2f} | packet delivery {eng.link.delivery:.0%} | one-way delay ~{eng.link.delay_s:.0f}s (simulated)</text>
  <text x="350" y="198" font-size="12" fill="#64748b" text-anchor="middle">{eng.link.reason}</text>
</svg></body></html>"""


def earth_card(eng):
    e = eng.earth
    state = eng.display_state()
    timer = ""
    if eng.down_since is not None and eng.restored_at is None:
        timer = f"{eng.tick - eng.down_since} s"
    elif eng.restored_at is not None:
        timer = f"restored in {eng.restored_at - eng.down_since} s"
    else:
        timer = "-"
    d = e.last_data or {}
    data = f"{d.get('temperature_c','-')} °C / {d.get('pressure_pa','-')} Pa" if d else "-"
    return f"""<div class="og-card"><h4>🌍 EARTH STATUS</h4>
{row('Connection', pill(STATE_TEXT[state], COLORS[state]))}
{row('Communication mode', e.mode)}
{row('Recovery attempts', e.attempts)}
{row('Current strategy', e.current_strategy)}
{row('Recovery timer', timer)}
{row('Last message', f'<span style="max-width:55%;text-align:right">{e.last_message}</span>')}
{row('Last mission data', data)}
{row('Received packets', len(e.received))}
{row('Missing packets', eng.missing_packets)}
{row('Restored (stored) packets', e.restored_packets)}
</div>"""


def stage_tracker(eng):
    order = [CHECK, DIAGNOSE, CHOOSE, TRY, VERIFY]
    if eng.agent is None:
        return '<div class="og-card"><h4>RECOVERY LOOP</h4><span style="color:#94a3b8">Earth-only mode: the probe has no onboard agent.</span></div>'
    a = eng.agent
    cells = []
    for i, s in enumerate(order):
        if a.state.startswith("COMMUNICATION") and a.phase == s:
            cls = "on"
        elif a.state.startswith("COMMUNICATION") and a.phase in order and order.index(a.phase) > i:
            cls = "done"
        elif not a.state.startswith("COMMUNICATION") and eng.restored_at is not None:
            cls = "done"
        else:
            cls = ""
        cells.append(f'<span class="og-stage {cls}">{s}</span>')
    cells.append(f'<span class="og-stage {"done" if eng.restored_at else ""}">RESTORED</span>')
    return f'<div class="og-card"><h4>ORBIT-GUARD RECOVERY LOOP</h4>{"".join(cells)}</div>'


def probe_card(eng):
    p = eng.probe
    a = eng.agent
    batt_color = "#22c55e" if p.battery > 40 else ("#eab308" if p.battery > 15 else "#ef4444")
    if a is None:
        ai = row("AI state", pill("NO AGENT (Earth-only mode)", "#64748b"))
        agent_html = ""
    else:
        ai = row("AI state", pill(a.state.replace("COMMUNICATION ", "COMM. "), "#a855f7" if a.state.startswith("COMM") else "#22c55e"))
        d = a.decision
        if d is None:
            agent_html = '<div style="color:#94a3b8;margin-top:.5rem">Monitoring - no action needed.</div>'
        else:
            alts = "".join(f"<div style='color:#64748b;font-size:.78rem'>· {l} ({c:.2f})</div>" for l, c in d.alternatives[:2])
            note = f"<div style='color:#a78bfa;font-size:.8rem'>LLM note: {d.llm_note}</div>" if d.llm_note else ""
            agent_html = f"""<div style="margin-top:.5rem;padding:.5rem;border:1px solid #6d28d9;border-radius:.5rem;background:#1e1038">
<div style="color:#c4b5fd;font-size:.75rem;letter-spacing:.1em">ORBIT-GUARD DECISION</div>
<div><b>ACTION:</b> {d.label}</div><div><b>REASON:</b> {d.reason}</div>
<div><b>CONFIDENCE:</b> {d.confidence:.2f} &nbsp; <b>PRIORITY:</b> {d.priority}</div>
{bar(d.confidence, '#a855f7')}
<div><b>EXPECTED RESULT:</b> {d.expected_result}</div>{note}{alts}</div>"""
    return f"""<div class="og-card"><h4>🛰️ PROBE + AI AGENT</h4>
{row('Battery', f'{p.battery:.0f}%')}{bar(p.battery/100, batt_color)}
{row('Communication', pill(STATE_TEXT[eng.display_state()], COLORS[eng.display_state()]))}
{row('Comm mode', p.mode)}
{row('Antenna', pill(p.antenna_status, status_color(p.antenna_status)))}
{row('Transmitter', pill(p.transmitter_status, status_color(p.transmitter_status)))}
{row('Receiver', pill(p.receiver_status, status_color(p.receiver_status)))}
{row('Temperature (sim.)', f'{p.temperature:.1f} °C')}
{row('Operating mode', p.operating_mode)}
{row('Stored data', f'{len(p.storage)} packets ({p.storage.size_kb} KB) / cap {p.storage.capacity}')}
{ai}{agent_html}</div>"""


def demo_steps_html(done):
    from app.simulation.demo import DEMO_STEPS
    items = "".join(f'<div class="og-step {"ok" if ok else ""}">{"✔" if ok else "○"} {i+1}. {t}</div>'
                    for i, (t, ok) in enumerate(zip(DEMO_STEPS, done)))
    return f'<div class="og-card"><h4>DEMO PROGRESS</h4>{items}</div>'


def event_log_html(log, n=40):
    lines = []
    for ev in reversed(log.events[-n:]):
        lines.append(f'<div style="color:{LOG_COLORS.get(ev.level, "#cbd5e1")}">{ev.clock} '
                     f'<b style="color:{SRC_COLORS.get(ev.source, "#94a3b8")}">[{ev.source}]</b> {ev.message}</div>')
    return f'<div class="og-log">{"".join(lines)}</div>'
