# ORBIT-GUARD - Quick Start (Windows)

1. Extract `ORBIT-GUARD_COMPLETE_PROJECT.zip` (right-click → Extract All).
2. Open the extracted **ORBIT-GUARD** folder in VS Code (File → Open Folder).
3. Double-click **setup.bat** (needs internet once). Wait for "Setup finished successfully".
4. Double-click **run.bat**. The dashboard opens in your browser.
5. Click **▶ START DEMO**.

Manual commands (VS Code terminal, Command Prompt):
```
cd ORBIT-GUARD
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/dashboard.py
```
Run tests: `python -m pytest`
Stuck? Read `docs/TROUBLESHOOTING.md`.
