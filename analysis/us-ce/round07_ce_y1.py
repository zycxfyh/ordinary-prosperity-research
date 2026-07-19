#!/usr/bin/env python3
"""Round 7 compatibility runner for the CE 2023 Y1 cloud execution.

This runner keeps the Round 6 fail-closed implementation intact while mapping
current official CE FMLI variable names to the aliases expected by that script.
The mappings are explicit and auditable; they do not synthesize missing values.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("round06_ce_y1.py")
spec = importlib.util.spec_from_file_location("round06_ce_y1", MODULE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"Unable to load {MODULE_PATH}")
round06 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = round06
spec.loader.exec_module(round06)

_original_load_file_family = round06.load_file_family


def load_file_family_with_current_aliases(specs, prefix):
    frame = _original_load_file_family(specs, prefix)
    if prefix.lower() != "fmli":
        return frame

    # Current official names documented by BLS.  Aliases exist only so the
    # Round 6 generic resolver can continue to enforce its normal gates.
    aliases = {
        "FINCATXM": "FINATXEM",   # after-tax family income, imputation mean
        "WAGRX": "FSALARYM",      # family wages and salaries, imputation mean
        "TRANCQ": "TRANSCQ",      # transportation current-quarter summary
        "TRANPQ": "TRANSPQ",      # transportation previous-quarter summary
    }
    for alias, source in aliases.items():
        if alias not in frame.columns and source in frame.columns:
            frame[alias] = frame[source]
    return frame


round06.load_file_family = load_file_family_with_current_aliases

if __name__ == "__main__":
    raise SystemExit(round06.main())
