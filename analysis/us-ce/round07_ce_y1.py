#!/usr/bin/env python3
"""Round 7 compatibility runner for the CE 2023 Y1 estimator.

The Round 6 implementation remains fail-closed. This runner maps current BLS
FMLI variable names to explicit aliases expected by that implementation.
No missing value is synthesized and no result is promoted beyond
``preliminary_interview_only``.
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

    aliases = {
        "FINCATXM": "FINATXEM",   # mean imputed family income after taxes
        "WAGRX": "FSALARYM",      # mean imputed family wages and salaries
        "TRANCQ": "TRANSCQ",      # transportation, current quarter
        "TRANPQ": "TRANSPQ",      # transportation, previous quarter
    }
    for alias, source in aliases.items():
        if alias not in frame.columns and source in frame.columns:
            frame[alias] = frame[source]
    return frame


round06.load_file_family = load_file_family_with_current_aliases

if __name__ == "__main__":
    raise SystemExit(round06.main())
