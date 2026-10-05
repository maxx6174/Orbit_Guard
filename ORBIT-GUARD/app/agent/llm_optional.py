"""OPTIONAL: ask a local Ollama model to phrase the agent's reasoning in plain English.

Disabled unless the environment variable ORBIT_GUARD_USE_OLLAMA=1 is set.
It NEVER changes the decision - it only adds a note. If Ollama is missing, we silently skip.
"""
import json
import os
import urllib.request


def enabled():
    return os.environ.get("ORBIT_GUARD_USE_OLLAMA", "0") == "1"


def explain(decision, causes_text, timeout=3.0):
    if not enabled():
        return ""
    model = os.environ.get("ORBIT_GUARD_OLLAMA_MODEL", "llama3.2")
    prompt = (f"In one short sentence, explain to a student why a simulated space probe chose to "
              f"'{decision.label}'. Diagnosis: {causes_text}. Do not claim it is guaranteed to work.")
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    try:
        req = urllib.request.Request("http://localhost:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read()).get("response", "").strip()[:240]
    except Exception:
        return ""
