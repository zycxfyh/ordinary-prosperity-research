#!/usr/bin/env python3
"""Round 8: construct preliminary 2023 US CE Y1 estimates from official ZIPs.

The script is fail-closed and produces aggregate-only outputs. It does not
commit, copy, or emit respondent-level records. Results remain
``preliminary_interview_only`` until Diary/source-selection integration and
income multiple-imputation variance checks are completed.

Example:
    python analysis/us-ce/round08_ce_y1.py \
      --target-year 2023 \
      --raw-dir data/raw/us-ce \
      --output-dir data/derived/us-ce/round08

Required input files in ``--raw-dir``:
    intrvw22.zip
    intrvw23.zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

REPLICATE_COLUMNS = [f"WTREP{i:02d}" for i in range(1, 45)]
TENURE_CODES = {
    1: "owner_with_mortgage",
    2: "owner_without_mortgage",
    3: "owner_mortgage_not_reported",
    4: "renter",
    5: "no_cash_rent",
    6: "student_housing",
}
INCOME_COLUMNS = {
    "FINCBTXM": "income_before_tax",
    "FINATXEM": "income_after_tax",
    "FSALARYM": "wages_salaries",
}
EXPENDITURE_STEMS = {
    "TOTEXP": "total_expenditure",
    "HOUS": "housing",
    "FOOD": "food",
    "TRANS": "transportation",
    "HEALTH": "healthcare",
    "RETPEN": "retirement_pension_social_security",
    "RENDWE": "rented_dwellings",
    "OWNDWE": "owned_dwellings",
    "UTIL": "utilities",
}
BASE_COLUMNS = [
    "NEWID",
    "AGE_REF",
    "FAM_SIZE",
    "NO_EARNR",
    "CUTENURE",
    "FINLWT21",
    "QINTRVYR",
    "QINTRVMO",
    *INCOME_COLUMNS,
    *REPLICATE_COLUMNS,
]


class ValidationError(RuntimeError):
    """Raised when a research validation gate fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-year", type=int, default=2023)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/us-ce"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/derived/us-ce/round08")
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expected_archives(target_year: int, raw_dir: Path) -> list[Path]:
    return [
        raw_dir / f"intrvw{str(target_year - 1)[-2:]}.zip",
        raw_dir / f"intrvw{str(target_year)[-2:]}.zip",
    ]


def required_fmli_suffixes(target_year: int) -> list[str]:
    yy = str(target_year)[-2:]
    next_yy = str(target_year + 1)[-2:]
    return [
        f"fmli{yy}1.csv",
        f"fmli{yy}2.csv",
        f"fmli{yy}3.csv",
        f"fmli{yy}4.csv",
        f"fmli{next_yy}1.csv",
    ]


def locate_members(archives: Sequence[Path], suffixes: Sequence[str]) -> list[tuple[Path, str]]:
    found: dict[str, tuple[Path, str]] = {}
    for archive_path in archives:
        if not archive_path.exists():
            raise ValidationError(f"Missing official archive: {archive_path}")
        if not zipfile.is_zipfile(archive_path):
            raise ValidationError(f"Invalid ZIP archive: {archive_path}")
        with zipfile.ZipFile(archive_path) as archive:
            for member in archive.namelist():
                lower = member.lower()
                for suffix in suffixes:
                    if lower.endswith(suffix.lower()):
                        if suffix in found:
                            raise ValidationError(
                                f"Duplicate FMLI member for {suffix}: {found[suffix]} and {(archive_path, member)}"
                            )
                        found[suffix] = (archive_path, member)
    missing = [suffix for suffix in suffixes if suffix not in found]
    if missing:
        raise ValidationError(f"Missing required FMLI files: {missing}")
    return [found[suffix] for suffix in suffixes]


def required_columns() -> list[str]:
    expenditure_columns = [
        f"{stem}{quarter}"
        for stem in EXPENDITURE_STEMS
        for quarter in ("CQ", "PQ")
    ]
    return [*BASE_COLUMNS, *expenditure_columns]


def load_fmli(members: Sequence[tuple[Path, str]]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    expected = required_columns()
    for archive_path, member in members:
        with zipfile.ZipFile(archive_path) as archive:
            header = pd.read_csv(archive.open(member), nrows=0)
            missing = [column for column in expected if column not in header.columns]
            if missing:
                raise ValidationError(f"{member}: missing required columns {missing}")
            frame = pd.read_csv(archive.open(member), usecols=expected, low_memory=False)
            frame["_SOURCE_ARCHIVE"] = archive_path.name
            frame["_SOURCE_MEMBER"] = member
            frames.append(frame)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if combined.empty:
        raise ValidationError("No FMLI records loaded")
    return combined


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def scope_months(frame: pd.DataFrame, target_year: int) -> pd.Series:
    year = numeric(frame, "QINTRVYR")
    month = numeric(frame, "QINTRVMO")
    output = pd.Series(0.0, index=frame.index)

    current = year.eq(target_year)
    output.loc[current & month.eq(2)] = 1
    output.loc[current & month.eq(3)] = 2
    output.loc[current & month.between(4, 12)] = 3

    fifth = year.eq(target_year + 1)
    output.loc[fifth & month.eq(1)] = 3
    output.loc[fifth & month.eq(2)] = 2
    output.loc[fifth & month.eq(3)] = 1
    return output


def calendar_expenditure(frame: pd.DataFrame, stem: str, target_year: int) -> pd.Series:
    cq = numeric(frame, f"{stem}CQ").fillna(0)
    pq = numeric(frame, f"{stem}PQ").fillna(0)
    year = numeric(frame, "QINTRVYR")
    month = numeric(frame, "QINTRVMO")
    output = pd.Series(0.0, index=frame.index)

    q1 = year.eq(target_year) & month.between(1, 3)
    output.loc[q1] = cq.loc[q1]

    q2_q4 = year.eq(target_year) & month.between(4, 12)
    output.loc[q2_q4] = cq.loc[q2_q4] + pq.loc[q2_q4]

    fifth = year.eq(target_year + 1) & month.between(1, 3)
    output.loc[fifth] = pq.loc[fifth]
    return output


def population(frame: pd.DataFrame, weight_column: str = "FINLWT21") -> float:
    weights = numeric(frame, weight_column).fillna(0)
    return float((weights / 4 * frame["MO_SCOPE"] / 3).sum())


def mean_income(frame: pd.DataFrame, column: str, weight_column: str = "FINLWT21") -> float:
    values = numeric(frame, column)
    weights = numeric(frame, weight_column)
    denominator_weights = weights / 4 * frame["MO_SCOPE"] / 3
    mask = values.notna() & denominator_weights.gt(0)
    if not mask.any():
        return math.nan
    return float(
        (values.loc[mask] * denominator_weights.loc[mask]).sum()
        / denominator_weights.loc[mask].sum()
    )


def mean_expenditure(
    frame: pd.DataFrame, column: str, weight_column: str = "FINLWT21"
) -> float:
    values = numeric(frame, column)
    weights = numeric(frame, weight_column)
    denominator = population(frame, weight_column)
    mask = values.notna() & weights.notna()
    if denominator <= 0 or not mask.any():
        return math.nan
    return float((values.loc[mask] * weights.loc[mask]).sum() / denominator)


def weighted_quantile(
    values: Iterable[float], weights: Iterable[float], quantiles: Sequence[float]
) -> list[float]:
    x = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    if not len(x):
        return [math.nan] * len(quantiles)
    order = np.argsort(x)
    x, w = x[order], w[order]
    cumulative = np.cumsum(w) - 0.5 * w
    cumulative /= w.sum()
    return [float(np.interp(quantile, cumulative, x)) for quantile in quantiles]


def brr_standard_error(frame: pd.DataFrame, column: str, kind: str) -> float:
    estimator = mean_income if kind == "income" else mean_expenditure
    full = estimator(frame, column)
    replicate_estimates = np.asarray(
        [estimator(frame, column, replicate) for replicate in REPLICATE_COLUMNS],
        dtype=float,
    )
    if not math.isfinite(full) or not np.isfinite(replicate_estimates).all():
        return math.nan
    return float(np.sqrt(np.mean((replicate_estimates - full) ** 2)))


def summarize_group(frame: pd.DataFrame, group_name: str) -> list[dict[str, object]]:
    base = {
        "group": group_name,
        "unweighted_interviews": len(frame),
        "unique_cu_ids": int(frame["CUID"].nunique()),
        "weighted_population": population(frame),
        "result_status": "preliminary_interview_only",
    }
    rows: list[dict[str, object]] = []

    distribution_weights = numeric(frame, "FINLWT21") / 4 * frame["MO_SCOPE"] / 3
    for column, label in INCOME_COLUMNS.items():
        estimate = mean_income(frame, column)
        standard_error = brr_standard_error(frame, column, "income")
        p25, median, p75 = weighted_quantile(
            numeric(frame, column), distribution_weights, [0.25, 0.5, 0.75]
        )
        rows.append(
            {
                **base,
                "measure": label,
                "mean": estimate,
                "p25": p25,
                "median": median,
                "p75": p75,
                "se": standard_error,
                "rse_pct": 100 * standard_error / abs(estimate)
                if estimate
                else math.nan,
                "ci95_low": estimate - 1.96 * standard_error,
                "ci95_high": estimate + 1.96 * standard_error,
                "method": "annual_income_scope_weighted",
                "variance_note": "sampling_only_income_imputation_variance_pending",
            }
        )

    for stem, label in EXPENDITURE_STEMS.items():
        column = f"{stem}_CY"
        estimate = mean_expenditure(frame, column)
        standard_error = brr_standard_error(frame, column, "expenditure")
        rows.append(
            {
                **base,
                "measure": label,
                "mean": estimate,
                "p25": math.nan,
                "median": math.nan,
                "p75": math.nan,
                "se": standard_error,
                "rse_pct": 100 * standard_error / abs(estimate)
                if estimate
                else math.nan,
                "ci95_low": estimate - 1.96 * standard_error,
                "ci95_high": estimate + 1.96 * standard_error,
                "method": "calendar_scope_expenditure_mean",
                "variance_note": "brr_sampling_variance",
            }
        )
    return rows


def make_group_accounting(estimates: pd.DataFrame) -> pd.DataFrame:
    wide = estimates.pivot(index="group", columns="measure", values="mean")
    required = [
        "income_after_tax",
        "total_expenditure",
        "retirement_pension_social_security",
        "housing",
    ]
    for column in required:
        if column not in wide:
            wide[column] = math.nan
    wide["reported_residual_mean_difference"] = (
        wide["income_after_tax"] - wide["total_expenditure"]
    )
    wide["residual_excluding_retirement_category"] = wide["income_after_tax"] - (
        wide["total_expenditure"] - wide["retirement_pension_social_security"]
    )
    wide["housing_share_after_tax_pct"] = (
        100 * wide["housing"] / wide["income_after_tax"]
    )
    wide["total_exp_share_after_tax_pct"] = (
        100 * wide["total_expenditure"] / wide["income_after_tax"]
    )
    return wide.reset_index()


def write_outputs(
    frame: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
    archives: Sequence[Path],
    members: Sequence[tuple[Path, str]],
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    estimate_rows: list[dict[str, object]] = []
    sample_rows: list[dict[str, object]] = []
    for group_name, group_frame in groups.items():
        if not group_frame.empty:
            estimate_rows.extend(summarize_group(group_frame, group_name))
        sample_rows.append(
            {
                "group": group_name,
                "interviews": len(group_frame),
                "unique_cu": int(group_frame["CUID"].nunique())
                if not group_frame.empty
                else 0,
                "population": population(group_frame)
                if not group_frame.empty
                else 0.0,
                "tenure_counts": json.dumps(
                    group_frame["HOUSING_GROUP"].value_counts(dropna=False).to_dict()
                    if not group_frame.empty
                    else {},
                    sort_keys=True,
                ),
            }
        )

    estimates = pd.DataFrame(estimate_rows)
    estimates.to_csv(output_dir / "preliminary_y1_estimates.csv", index=False)
    make_group_accounting(estimates).to_csv(
        output_dir / "group_accounting.csv", index=False
    )
    pd.DataFrame(sample_rows).to_csv(output_dir / "sample_audit.csv", index=False)

    manifest = {
        "result_status": "preliminary_interview_only",
        "in_scope_interviews": len(frame),
        "archives": [
            {
                "file": archive.name,
                "bytes": archive.stat().st_size,
                "sha256": sha256_file(archive),
            }
            for archive in archives
        ],
        "fmli_members": [
            {"archive": archive.name, "member": member}
            for archive, member in members
        ],
    }
    (output_dir / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    archives = expected_archives(args.target_year, args.raw_dir)
    members = locate_members(archives, required_fmli_suffixes(args.target_year))
    frame = load_fmli(members)

    frame["MO_SCOPE"] = scope_months(frame, args.target_year)
    frame = frame.loc[frame["MO_SCOPE"].gt(0)].copy()
    frame["CUID"] = (numeric(frame, "NEWID").astype("Int64") // 10).astype("string")

    observed_tenure = sorted(
        numeric(frame, "CUTENURE").dropna().astype(int).unique().tolist()
    )
    unknown_tenure = [code for code in observed_tenure if code not in TENURE_CODES]
    if unknown_tenure:
        raise ValidationError(f"Unknown CUTENURE codes: {unknown_tenure}")
    frame["HOUSING_GROUP"] = numeric(frame, "CUTENURE").map(TENURE_CODES)

    for stem in EXPENDITURE_STEMS:
        frame[f"{stem}_CY"] = calendar_expenditure(frame, stem, args.target_year)

    benchmark = frame.loc[
        numeric(frame, "AGE_REF").between(25, 34)
        & numeric(frame, "FAM_SIZE").eq(1)
    ].copy()
    y1 = benchmark.loc[numeric(benchmark, "NO_EARNR").ge(1)].copy()
    if benchmark.empty or y1.empty:
        raise ValidationError("Benchmark or Y1 sample is empty")

    groups = {
        "benchmark_all_one_person_25_34": benchmark,
        "y1_all": y1,
        "y1_renter": y1.loc[y1["HOUSING_GROUP"].eq("renter")],
        "y1_owner_with_mortgage": y1.loc[
            y1["HOUSING_GROUP"].eq("owner_with_mortgage")
        ],
        "y1_owner_without_mortgage": y1.loc[
            y1["HOUSING_GROUP"].eq("owner_without_mortgage")
        ],
        "y1_no_cash_rent": y1.loc[y1["HOUSING_GROUP"].eq("no_cash_rent")],
        "y1_student_housing": y1.loc[
            y1["HOUSING_GROUP"].eq("student_housing")
        ],
    }
    write_outputs(frame, groups, archives, members, args.output_dir)
    print(f"Loaded {len(frame):,} in-scope interview records")
    print(f"Wrote aggregate-only outputs to {args.output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        raise SystemExit(f"VALIDATION FAILED: {exc}") from exc
