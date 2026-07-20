#!/usr/bin/env python3
"""Round 10: integrate all published 2023 CE expenditure UCCs.

The estimator reads the official 2023 integrated hierarchical grouping to
resolve each UCC's source survey and annualization factor. Interview and Diary
microdata remain independent samples: estimates are produced separately and
combined only at the estimate/variance level.

No respondent-level data are written. The run fails closed unless the all-CU
integrated total reproduces the official 2023 total expenditure within the
configured tolerance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from round09_diary_food_integration import (
    REPLICATES,
    ValidationError,
    group_masks,
    load_diary,
    load_interview,
    normalize_newid,
    validate_zip,
)

OFFICIAL_TOTAL_EXPENDITURE_2023 = 77_280.0
VALID_SOURCES = {"I", "D"}
VALID_FACTORS = {1.0, 4.0}
VALID_EXPENDITURE_SECTIONS = {"FOOD", "EXPEND"}
GENERIC_ROOT_NAMES = {
    "average annual expenditures",
    "average annual expenditures per consumer unit",
    "total expenditures",
}


@dataclass(frozen=True)
class UccRule:
    ucc: str
    source: str
    factor: float
    section: str
    level: int
    name: str
    hierarchy_path: str
    top_category: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interview-2022", type=Path, default=Path("data/raw/us-ce/intrvw22.zip"))
    parser.add_argument("--interview-2023", type=Path, default=Path("data/raw/us-ce/intrvw23.zip"))
    parser.add_argument("--diary-2023", type=Path, default=Path("data/raw/us-ce/diary23.zip"))
    parser.add_argument("--hierarchical-groupings", type=Path, default=Path("data/raw/us-ce/stubs.zip"))
    parser.add_argument("--source-selection", type=Path, default=Path("data/raw/us-ce/ce_source_integrate.xlsx"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/derived/us-ce/round10"))
    parser.add_argument("--official-total", type=float, default=OFFICIAL_TOTAL_EXPENDITURE_2023)
    parser.add_argument("--validation-tolerance-pct", type=float, default=1.0)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_binary(path: Path, expected_suffix: str) -> dict[str, object]:
    if not path.exists():
        raise ValidationError(f"Missing input file: {path}")
    if path.suffix.lower() != expected_suffix:
        raise ValidationError(f"Expected {expected_suffix} input, got {path}")
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "format": expected_suffix.removeprefix("."),
    }


def _slice(line: str, start_position: int, end_position_exclusive: int | None = None) -> str:
    """Slice a fixed-width line using one-based BLS start positions."""
    start = start_position - 1
    end = None if end_position_exclusive is None else end_position_exclusive - 1
    return line[start:end]


def _normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _top_category(path: list[str], leaf_name: str) -> str:
    candidates = [item for item in path if item and item.lower() not in GENERIC_ROOT_NAMES]
    if candidates:
        return candidates[0]
    return leaf_name or "unclassified"


def parse_integrated_grouping_text(text: str) -> pd.DataFrame:
    """Parse one official CE-HG-Integ fixed-width text file.

    BLS documents the start positions as: type=1, level=4, name=7,
    UCC=70, source=83, factor=86, and section=89.
    """
    hierarchy: dict[int, str] = {}
    rules: list[UccRule] = []

    for line_number, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip() or raw.startswith("*"):
            continue
        line = raw.rstrip("\r\n")
        record_type = _slice(line, 1, 2).strip()
        level_raw = _slice(line, 4, 5).strip()
        name = _normalize_name(_slice(line, 7, 70))
        ucc = _slice(line, 70, 76).strip()
        source = _slice(line, 83, 84).strip().upper()
        factor_raw = _slice(line, 86, 87).strip()
        section = _slice(line, 89).strip().upper()

        if not level_raw.isdigit():
            continue
        level = int(level_raw)
        if not 1 <= level <= 9:
            raise ValidationError(f"Grouping line {line_number}: invalid level {level}")

        if record_type == "2" and hierarchy.get(level):
            hierarchy[level] = _normalize_name(f"{hierarchy[level]} {name}")
        elif name:
            hierarchy[level] = name
        for stale_level in [key for key in hierarchy if key > level]:
            del hierarchy[stale_level]

        if not re.fullmatch(r"\d{6}", ucc):
            continue
        if source not in VALID_SOURCES:
            continue
        try:
            factor = float(factor_raw)
        except ValueError as exc:
            raise ValidationError(
                f"Grouping line {line_number}, UCC {ucc}: invalid factor {factor_raw!r}"
            ) from exc
        if factor not in VALID_FACTORS:
            raise ValidationError(
                f"Grouping line {line_number}, UCC {ucc}: unsupported factor {factor}"
            )
        if section not in VALID_EXPENDITURE_SECTIONS:
            continue

        path = [hierarchy[key] for key in sorted(hierarchy) if hierarchy[key]]
        leaf_name = name or hierarchy.get(level, "")
        rules.append(
            UccRule(
                ucc=ucc,
                source=source,
                factor=factor,
                section=section,
                level=level,
                name=leaf_name,
                hierarchy_path=" > ".join(path),
                top_category=_top_category(path[:-1], leaf_name),
            )
        )

    if not rules:
        raise ValidationError("Integrated grouping parser produced no expenditure UCC rules")

    frame = pd.DataFrame([rule.__dict__ for rule in rules])
    resolved_rows: list[pd.Series] = []
    for ucc, group in frame.groupby("ucc", sort=True, observed=True):
        signatures = group[["source", "factor"]].drop_duplicates()
        if len(signatures) != 1:
            raise ValidationError(
                f"Conflicting integrated grouping rules for UCC {ucc}: "
                f"{signatures.to_dict(orient='records')}"
            )
        # A UCC can appear in more than one published hierarchy. Count it once.
        # Prefer EXPEND over FOOD because it is the comprehensive expenditure tree.
        ordered = group.assign(_priority=group["section"].map({"EXPEND": 0, "FOOD": 1}))
        resolved_rows.append(ordered.sort_values(["_priority", "level"]).iloc[0].drop(labels="_priority"))

    resolved = pd.DataFrame(resolved_rows).reset_index(drop=True)
    if resolved["ucc"].duplicated().any():
        raise ValidationError("Integrated grouping resolution left duplicate UCCs")
    if set(resolved["source"]) - VALID_SOURCES:
        raise ValidationError("Integrated grouping resolution contains unsupported sources")
    return resolved.sort_values("ucc").reset_index(drop=True)


def load_integrated_grouping(path: Path, target_year: int = 2023) -> tuple[pd.DataFrame, dict[str, object]]:
    manifest = validate_zip(path)
    with zipfile.ZipFile(path) as archive:
        candidates = [
            member
            for member in archive.namelist()
            if re.search(rf"CE-HG-Integ-{target_year}\.txt$", member, flags=re.IGNORECASE)
        ]
        if len(candidates) != 1:
            raise ValidationError(
                f"Expected exactly one CE-HG-Integ-{target_year}.txt in {path}; found {candidates}"
            )
        member = candidates[0]
        text = archive.read(member).decode("latin-1")
    rules = parse_integrated_grouping_text(text)
    manifest.update(
        {
            "role": "official_integrated_hierarchical_grouping",
            "selected_member": member,
            "parsed_ucc_count": int(len(rules)),
            "interview_ucc_count": int(rules["source"].eq("I").sum()),
            "diary_ucc_count": int(rules["source"].eq("D").sum()),
        }
    )
    return rules, manifest


def audit_source_selection_workbook(path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    manifest = validate_binary(path, ".xlsx")
    try:
        workbook = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:  # pragma: no cover - backend-specific detail
        raise ValidationError(f"Cannot read source-selection workbook {path}: {exc}") from exc

    rows: list[dict[str, object]] = []
    for sheet in workbook.sheet_names:
        preview = pd.read_excel(workbook, sheet_name=sheet, header=None)
        nonempty = preview.dropna(how="all").dropna(axis=1, how="all")
        rows.append(
            {
                "sheet": sheet,
                "row_count": int(nonempty.shape[0]),
                "column_count": int(nonempty.shape[1]),
                "nonempty_cells": int(nonempty.notna().sum().sum()),
            }
        )
    audit = pd.DataFrame(rows)
    if audit.empty or audit["nonempty_cells"].sum() == 0:
        raise ValidationError("Source-selection workbook contains no non-empty cells")
    manifest.update(
        {
            "role": "official_source_selection_secondary_crosscheck",
            "sheet_count": int(len(audit)),
            "status": "metadata_loaded_secondary_crosscheck",
        }
    )
    return audit, manifest


def _prepare_detail(detail: pd.DataFrame, rules: pd.DataFrame, survey_source: str) -> pd.DataFrame:
    selected_rules = rules.loc[rules["source"].eq(survey_source)].copy()
    if selected_rules.empty:
        raise ValidationError(f"No {survey_source} UCCs in integrated grouping")
    merged = detail.merge(
        selected_rules[["ucc", "factor", "top_category", "hierarchy_path"]],
        left_on="UCC6",
        right_on="ucc",
        how="inner",
        validate="many_to_one",
    )
    merged["COST"] = pd.to_numeric(merged["COST"], errors="coerce").fillna(0.0)
    if survey_source == "D":
        # Diary records are weekly. BLS methodology first inflates by 13 to a
        # quarterly amount; the official grouping factor then annualizes it.
        merged["ANNUALIZED_COST"] = merged["COST"] * 13.0 * merged["factor"]
    else:
        # Interview detail is brought into the target calendar year by REF_YR
        # in Round 9's loader; apply the official grouping factor to each UCC.
        merged["ANNUALIZED_COST"] = merged["COST"] * merged["factor"]
    return merged


def _attach_aggregates(
    family: pd.DataFrame,
    detail: pd.DataFrame,
    *,
    total_column: str,
    category_prefix: str,
) -> list[str]:
    total = detail.groupby("NEWID_STR", observed=True)["ANNUALIZED_COST"].sum()
    family[total_column] = family["NEWID_STR"].map(total).fillna(0.0)

    category_columns: list[str] = []
    category_totals = detail.groupby(
        ["NEWID_STR", "top_category"], observed=True
    )["ANNUALIZED_COST"].sum()
    for index, category in enumerate(sorted(detail["top_category"].dropna().unique())):
        column = f"{category_prefix}_{index:03d}"
        values = category_totals.xs(category, level="top_category", drop_level=True)
        family[column] = family["NEWID_STR"].map(values).fillna(0.0)
        category_columns.append(column)
        family.attrs.setdefault("category_labels", {})[column] = category
    return category_columns


def population(frame: pd.DataFrame, survey: str, weight: str = "FINLWT21") -> float:
    w = pd.to_numeric(frame[weight], errors="coerce").fillna(0.0)
    if survey == "interview":
        return float((w / 4.0 * frame["MO_SCOPE"] / 3.0).sum())
    if survey == "diary":
        return float((w / 4.0).sum())
    raise ValueError(f"Unknown survey {survey}")


def weighted_mean(frame: pd.DataFrame, column: str, survey: str, weight: str = "FINLWT21") -> float:
    denominator = population(frame, survey, weight)
    if not math.isfinite(denominator) or denominator <= 0:
        return math.nan
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    weights = pd.to_numeric(frame[weight], errors="coerce").fillna(0.0)
    return float((values * weights).sum() / denominator)


def brr_se(frame: pd.DataFrame, column: str, survey: str) -> float:
    full = weighted_mean(frame, column, survey)
    replicates = np.asarray(
        [weighted_mean(frame, column, survey, replicate) for replicate in REPLICATES],
        dtype=float,
    )
    if not math.isfinite(full) or not np.isfinite(replicates).all():
        return math.nan
    return float(np.sqrt(np.mean((replicates - full) ** 2)))


def combine_independent(
    interview_frame: pd.DataFrame,
    diary_frame: pd.DataFrame,
    interview_column: str,
    diary_column: str,
) -> dict[str, float]:
    i_mean = weighted_mean(interview_frame, interview_column, "interview")
    d_mean = weighted_mean(diary_frame, diary_column, "diary")
    i_se = brr_se(interview_frame, interview_column, "interview")
    d_se = brr_se(diary_frame, diary_column, "diary")
    combined = i_mean + d_mean
    combined_se = (
        math.sqrt(i_se**2 + d_se**2)
        if math.isfinite(i_se) and math.isfinite(d_se)
        else math.nan
    )
    return {
        "interview_component_mean": i_mean,
        "interview_component_se": i_se,
        "diary_component_mean": d_mean,
        "diary_component_se": d_se,
        "combined_mean": combined,
        "combined_se": combined_se,
    }


def _estimate_status(group: str, combined: float, combined_se: float, total_validated: bool) -> str:
    if group == "all_consumer_units":
        return "integrated_expenditure_validated" if total_validated else "validation_failed"
    if not total_validated:
        return "blocked_by_all_cu_validation"
    if not combined or not math.isfinite(combined_se):
        return "exploratory_unstable"
    rse = abs(100.0 * combined_se / combined)
    if rse <= 20.0:
        return "supported_preliminary_descriptive"
    if rse <= 30.0:
        return "exploratory_high_rse"
    return "blocked_unstable_cell"


def _source_coverage(detail: pd.DataFrame, rules: pd.DataFrame, source: str) -> pd.DataFrame:
    expected = rules.loc[rules["source"].eq(source), ["ucc", "factor", "top_category"]].copy()
    observed_counts = detail.groupby("UCC6", observed=True).size().rename("raw_record_count")
    expected["raw_record_count"] = expected["ucc"].map(observed_counts).fillna(0).astype(int)
    expected["observed_in_raw_data"] = expected["raw_record_count"].gt(0)
    expected["source"] = source
    return expected


def run(args: argparse.Namespace) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_manifest: list[dict[str, object]] = [
        validate_zip(args.interview_2022),
        validate_zip(args.interview_2023),
        validate_zip(args.diary_2023),
    ]
    rules, grouping_manifest = load_integrated_grouping(args.hierarchical_groupings)
    workbook_audit, source_selection_manifest = audit_source_selection_workbook(args.source_selection)
    source_manifest.extend([grouping_manifest, source_selection_manifest])

    rules.to_csv(args.output_dir / "issue-04-round-10-ucc-source-map.csv", index=False)
    workbook_audit.to_csv(
        args.output_dir / "issue-04-round-10-source-selection-audit.csv", index=False
    )
    (args.output_dir / "issue-04-round-10-source-manifest.json").write_text(
        json.dumps(source_manifest, indent=2), encoding="utf-8"
    )

    interview, mtbi = load_interview(args.interview_2022, args.interview_2023)
    diary, expd = load_diary(args.diary_2023)
    mtbi["NEWID_STR"] = normalize_newid(mtbi["NEWID"])
    expd["NEWID_STR"] = normalize_newid(expd["NEWID"])

    interview_detail = _prepare_detail(mtbi, rules, "I")
    diary_detail = _prepare_detail(expd, rules, "D")
    _attach_aggregates(
        interview,
        interview_detail,
        total_column="I_INTEGRATED_EXPENDITURE",
        category_prefix="I_CATEGORY",
    )
    _attach_aggregates(
        diary,
        diary_detail,
        total_column="D_INTEGRATED_EXPENDITURE",
        category_prefix="D_CATEGORY",
    )

    coverage = pd.concat(
        [
            _source_coverage(mtbi, rules, "I"),
            _source_coverage(expd, rules, "D"),
        ],
        ignore_index=True,
    )
    coverage.to_csv(args.output_dir / "issue-04-round-10-ucc-coverage.csv", index=False)

    interview_masks = group_masks(interview)
    diary_masks = group_masks(diary)
    sample_rows: list[dict[str, object]] = []
    raw_total_results: dict[str, dict[str, float]] = {}
    for group in interview_masks:
        i_group = interview.loc[interview_masks[group]].copy()
        d_group = diary.loc[diary_masks[group]].copy()
        sample_rows.append(
            {
                "group": group,
                "interview_records": len(i_group),
                "interview_unique_cu": i_group["NEWID_STR"].str[:-1].nunique(),
                "interview_population": population(i_group, "interview"),
                "diary_week_records": len(d_group),
                "diary_unique_cu": d_group["NEWID_STR"].str[:-1].nunique(),
                "diary_population": population(d_group, "diary"),
            }
        )
        raw_total_results[group] = combine_independent(
            i_group,
            d_group,
            "I_INTEGRATED_EXPENDITURE",
            "D_INTEGRATED_EXPENDITURE",
        )

    all_cu_estimate = raw_total_results["all_consumer_units"]["combined_mean"]
    percent_difference = 100.0 * (all_cu_estimate / args.official_total - 1.0)
    total_validated = abs(percent_difference) <= args.validation_tolerance_pct
    validation = pd.DataFrame(
        [
            {
                "measure": "total_expenditure",
                "pumd_estimate": all_cu_estimate,
                "official_2023_value": args.official_total,
                "absolute_difference": all_cu_estimate - args.official_total,
                "percent_difference": percent_difference,
                "validation_threshold_pct": args.validation_tolerance_pct,
                "status": "pass" if total_validated else "fail",
            }
        ]
    )
    validation.to_csv(args.output_dir / "issue-04-round-10-validation.csv", index=False)

    estimate_rows: list[dict[str, object]] = []
    for group, result in raw_total_results.items():
        combined = result["combined_mean"]
        combined_se = result["combined_se"]
        estimate_rows.append(
            {
                "group": group,
                "measure": "total_expenditure_integrated",
                **result,
                "rse_pct": 100.0 * combined_se / abs(combined)
                if combined and math.isfinite(combined_se)
                else math.nan,
                "ci95_low": combined - 1.96 * combined_se
                if math.isfinite(combined_se)
                else math.nan,
                "ci95_high": combined + 1.96 * combined_se
                if math.isfinite(combined_se)
                else math.nan,
                "status": _estimate_status(group, combined, combined_se, total_validated),
                "interpretation": "group mean; not an individual annual cash-flow residual",
            }
        )
    pd.DataFrame(estimate_rows).to_csv(
        args.output_dir / "issue-04-round-10-group-total-estimates.csv", index=False
    )
    pd.DataFrame(sample_rows).to_csv(
        args.output_dir / "issue-04-round-10-sample-audit.csv", index=False
    )

    # Category estimates are kept separate because names and nesting are owned
    # by the official hierarchy and may change by year.
    i_labels: Mapping[str, str] = interview.attrs.get("category_labels", {})
    d_labels: Mapping[str, str] = diary.attrs.get("category_labels", {})
    category_names = sorted(set(i_labels.values()) | set(d_labels.values()))
    category_rows: list[dict[str, object]] = []
    for group in interview_masks:
        i_group = interview.loc[interview_masks[group]].copy()
        d_group = diary.loc[diary_masks[group]].copy()
        for category in category_names:
            i_column = next((col for col, label in i_labels.items() if label == category), None)
            d_column = next((col for col, label in d_labels.items() if label == category), None)
            if i_column is None:
                i_group["_ZERO_I"] = 0.0
                i_column = "_ZERO_I"
            if d_column is None:
                d_group["_ZERO_D"] = 0.0
                d_column = "_ZERO_D"
            result = combine_independent(i_group, d_group, i_column, d_column)
            combined = result["combined_mean"]
            combined_se = result["combined_se"]
            category_rows.append(
                {
                    "group": group,
                    "category": category,
                    **result,
                    "rse_pct": 100.0 * combined_se / abs(combined)
                    if combined and math.isfinite(combined_se)
                    else math.nan,
                    "status": _estimate_status(group, combined, combined_se, total_validated),
                }
            )
    pd.DataFrame(category_rows).to_csv(
        args.output_dir / "issue-04-round-10-category-estimates.csv", index=False
    )

    # All-CU UCC-level audit. Factors are applied before aggregation; standard
    # errors use the same 44 replicate weights as the total estimator.
    ucc_rows: list[dict[str, object]] = []
    for source, family, detail, survey in [
        ("I", interview, interview_detail, "interview"),
        ("D", diary, diary_detail, "diary"),
    ]:
        for ucc, ucc_detail in detail.groupby("ucc", observed=True):
            temp_column = "_TEMP_UCC"
            values = ucc_detail.groupby("NEWID_STR", observed=True)["ANNUALIZED_COST"].sum()
            family[temp_column] = family["NEWID_STR"].map(values).fillna(0.0)
            rule = rules.loc[rules["ucc"].eq(ucc)].iloc[0]
            mean = weighted_mean(family, temp_column, survey)
            se = brr_se(family, temp_column, survey)
            ucc_rows.append(
                {
                    "ucc": ucc,
                    "source": source,
                    "factor": rule["factor"],
                    "name": rule["name"],
                    "top_category": rule["top_category"],
                    "hierarchy_path": rule["hierarchy_path"],
                    "annual_mean": mean,
                    "brr_se": se,
                    "rse_pct": 100.0 * se / abs(mean)
                    if mean and math.isfinite(se)
                    else math.nan,
                    "raw_record_count": len(ucc_detail),
                }
            )
    pd.DataFrame(ucc_rows).to_csv(
        args.output_dir / "issue-04-round-10-ucc-estimates-all-cu.csv", index=False
    )

    print(validation.to_string(index=False))
    if not total_validated:
        raise ValidationError(
            "Full expenditure integration did not reproduce the official 2023 total:\n"
            + validation.to_string(index=False)
        )
    return 0


def main() -> int:
    return run(parse_args())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        raise SystemExit(f"VALIDATION FAILED: {exc}") from exc
