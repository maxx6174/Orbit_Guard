# Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Install Python 3.13 from python.org and tick **Add python.exe to PATH**; reopen the terminal. `setup.bat` also tries `py -3`. |
| `.venv\Scripts\activate` blocked in PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or use Command Prompt (`cmd`). |
| `pip install` fails / no internet | Install needs internet once. Behind a proxy/college network: try a phone hotspot. |
| `streamlit` is not recognised | Activate the venv first, or run `python -m streamlit run app/dashboard.py`. |
| Port 8501 in use | `streamlit run app/dashboard.py --server.port 8502` |
| `ModuleNotFoundError: app` | Run commands from the **ORBIT-GUARD** folder (the one that contains `app/`). |
| Page flickers/slow | Set **Pace = Normal/Slow**; close other heavy tabs. |
| Dashboard looks stuck | Click **↺ RESET MISSION**, then **▶ START DEMO**. |
| Tests fail on import | Run `python -m pytest` from the project folder, with the venv active. |
| Ollama note never appears | It is optional: install Ollama, `ollama pull llama3.2`, `set ORBIT_GUARD_USE_OLLAMA=1` before launching. |
