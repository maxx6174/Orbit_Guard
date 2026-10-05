"""Command-line comparison (no dashboard needed):  python tools/compare_cli.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.compare import all_faults_matrix  # noqa: E402

if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(f"ORBIT-GUARD simulation comparison (seed {seed}) - SOFTWARE SIMULATION, not real space data\n")
    print(all_faults_matrix(seed).to_string(index=False))
