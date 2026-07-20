from __future__ import annotations

import importlib.util
import math
import sys
import types
from pathlib import Path

import pandas as pd
import pytest


# Round 10 imports the existing Round 9 runtime. Parser and estimator unit tests
# inject the minimal contract so the tests remain isolated from raw microdata.
stub = types.ModuleType("round09_diary_food_integration")
stub.REPLICATES = [f"WTREP{i:02d}" for i in range(1, 45)]


class ValidationError(RuntimeError):
    pass


stub.ValidationError = ValidationError
stub.group_masks = lambda frame: {}
stub.load_diary = lambda *args, **kwargs: None
stub.load_interview = lambda *args, **kwargs: None
stub.normalize_newid = lambda series: series.astype(str)
stub.validate_zip = lambda path: {"file": Path(path).name}
sys.modules[stub.__name__] = stub

MODULE_PATH = Path(__file__).parents[1] / "analysis" / "us-ce" / "round10_full_expenditure_integration.py"
spec = importlib.util.spec_from_file_location("round10", MODULE_PATH)
round10 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = round10
spec.loader.exec_module(round10)


def fixed_width_line(
    *,
    level: int,
    name: str,
    ucc: str = "",
    source: str = "G",
    factor: str = "",
    section: str = "EXPEND",
    record_type: str = "1",
) -> str:
    chars = [" "] * 120
    chars[0] = record_type
    chars[3] = str(level)
    chars[6 : 6 + len(name)] = name
    chars[69 : 69 + len(ucc)] = ucc
    chars[82 : 82 + len(source)] = source
    chars[85 : 85 + len(factor)] = factor
    chars[88 : 88 + len(section)] = section
    return "".join(chars)


def test_parse_integrated_grouping_resolves_source_factor_and_path() -> None:
    text = "\n".join(
        [
            fixed_width_line(level=1, name="Average annual expenditures"),
            fixed_width_line(level=2, name="Food"),
            fixed_width_line(
                level=3,
                name="Bread",
                ucc="010110",
                source="D",
                factor="4",
                section="FOOD",
            ),
            fixed_width_line(level=2, name="Housing"),
            fixed_width_line(
                level=3,
                name="Rent",
                ucc="210110",
                source="I",
                factor="1",
                section="EXPEND",
            ),
        ]
    )

    result = round10.parse_integrated_grouping_text(text).set_index("ucc")

    assert result.loc["010110", "source"] == "D"
    assert result.loc["010110", "factor"] == 4.0
    assert result.loc["010110", "top_category"] == "Food"
    assert "Average annual expenditures > Food > Bread" in result.loc["010110", "hierarchy_path"]
    assert result.loc["210110", "source"] == "I"
    assert result.loc["210110", "factor"] == 1.0


def test_duplicate_ucc_with_same_rule_is_counted_once_and_prefers_expend() -> None:
    text = "\n".join(
        [
            fixed_width_line(level=1, name="Average annual expenditures"),
            fixed_width_line(level=2, name="Food"),
            fixed_width_line(
                level=3,
                name="Meals",
                ucc="190400",
                source="D",
                factor="4",
                section="FOOD",
            ),
            fixed_width_line(level=2, name="Total expenditures"),
            fixed_width_line(
                level=3,
                name="Meals",
                ucc="190400",
                source="D",
                factor="4",
                section="EXPEND",
            ),
        ]
    )

    result = round10.parse_integrated_grouping_text(text)

    assert result["ucc"].tolist() == ["190400"]
    assert result.loc[0, "section"] == "EXPEND"


def test_conflicting_duplicate_ucc_fails_closed() -> None:
    text = "\n".join(
        [
            fixed_width_line(
                level=2,
                name="Conflicting item",
                ucc="999999",
                source="I",
                factor="1",
                section="EXPEND",
            ),
            fixed_width_line(
                level=2,
                name="Conflicting item",
                ucc="999999",
                source="D",
                factor="4",
                section="FOOD",
            ),
        ]
    )

    with pytest.raises(ValidationError, match="Conflicting integrated grouping rules"):
        round10.parse_integrated_grouping_text(text)


def test_prepare_detail_applies_official_annualization_factors() -> None:
    rules = pd.DataFrame(
        [
            {"ucc": "111111", "source": "I", "factor": 4.0, "top_category": "A", "hierarchy_path": "A"},
            {"ucc": "222222", "source": "D", "factor": 4.0, "top_category": "B", "hierarchy_path": "B"},
        ]
    )
    interview = pd.DataFrame({"UCC6": ["111111"], "COST": [10.0], "NEWID_STR": ["1"]})
    diary = pd.DataFrame({"UCC6": ["222222"], "COST": [10.0], "NEWID_STR": ["2"]})

    prepared_i = round10._prepare_detail(interview, rules, "I")
    prepared_d = round10._prepare_detail(diary, rules, "D")

    assert prepared_i.loc[0, "ANNUALIZED_COST"] == 40.0
    assert prepared_d.loc[0, "ANNUALIZED_COST"] == 520.0


def test_combine_independent_adds_means_and_variances(monkeypatch: pytest.MonkeyPatch) -> None:
    means = iter([100.0, 40.0])
    ses = iter([3.0, 4.0])
    monkeypatch.setattr(round10, "weighted_mean", lambda *args, **kwargs: next(means))
    monkeypatch.setattr(round10, "brr_se", lambda *args, **kwargs: next(ses))

    result = round10.combine_independent(pd.DataFrame(), pd.DataFrame(), "i", "d")

    assert result["combined_mean"] == 140.0
    assert math.isclose(result["combined_se"], 5.0)
