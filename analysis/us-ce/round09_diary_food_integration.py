#!/usr/bin/env python3
"""Round 9: integrate CE 2023 food estimates from Interview and Diary PUMD.

The script reproduces the published 2023 all-CU food totals by integrating
UCC-level estimates from the two independent CE surveys. It then estimates
food for the Y1 archetype: reference person age 25-34, one-person consumer
unit, and at least one earner.

Raw PUMD files are never written to outputs. Outputs contain only aggregate
estimates, source hashes, sample counts, and validation results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REPLICATES = [f"WTREP{i:02d}" for i in range(1, 45)]
TENURE = {
    1: "owner_with_mortgage",
    2: "owner_without_mortgage",
    3: "owner_mortgage_not_reported",
    4: "renter",
    5: "no_cash_rent",
    6: "student_housing",
}

# Reconstructed 2023 integrated food source-selection set. The all-CU result
# must reproduce the official BLS 2023 food-at-home, food-away, and total-food
# means within the validation threshold or the script fails.
INTERVIEW_HOME = {"190904"}
INTERVIEW_AWAY = {"190901", "190902", "190903", "190905", "790430", "800700"}
DIARY_AWAY = {"190400", "190500", "190600", "190700"}
OFFICIAL_2023 = {
    "food_at_home": 6053.0,
    "food_away_from_home": 3933.0,
    "food_total_integrated": 9985.0,
    "total_expenditure": 77280.0,
}


class ValidationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interview-2022", type=Path, default=Path("data/raw/us-ce/intrvw22.zip"))
    parser.add_argument("--interview-2023", type=Path, default=Path("data/raw/us-ce/intrvw23.zip"))
    parser.add_argument("--diary-2022", type=Path, default=Path("data/raw/us-ce/diary22.zip"))
    parser.add_argument("--diary-2023", type=Path, default=Path("data/raw/us-ce/diary23.zip"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/derived/us-ce/round09"))
    parser.add_argument("--validation-tolerance-pct", type=float, default=1.0)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_zip(path: Path) -> dict:
    if not path.exists():
        raise ValidationError(f"Missing input file: {path}")
    if not zipfile.is_zipfile(path):
        raise ValidationError(f"Not a ZIP archive: {path}")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValidationError(f"Corrupt ZIP member in {path}: {bad}")
        return {
            "file": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "zip_test": "pass",
            "member_count": len(archive.namelist()),
        }


def read_member(path: Path, member: str, usecols: Iterable[str] | None = None) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        if member not in archive.namelist():
            raise ValidationError(f"Missing member {member} in {path}")
        header = pd.read_csv(archive.open(member), nrows=0)
        if usecols is not None:
            missing = sorted(set(usecols) - set(header.columns))
            if missing:
                raise ValidationError(f"{member}: missing columns {missing}")
        frame = pd.read_csv(archive.open(member), usecols=usecols, low_memory=False)
    frame["_SOURCE"] = member
    frame.columns = [str(c).upper() if c != "_SOURCE" else c for c in frame.columns]
    return frame


def normalize_newid(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(8)


def scope_months(year: pd.Series, month: pd.Series) -> pd.Series:
    y = pd.to_numeric(year, errors="coerce")
    m = pd.to_numeric(month, errors="coerce")
    out = pd.Series(0.0, index=year.index)
    current = y.eq(2023)
    out.loc[current & m.eq(2)] = 1
    out.loc[current & m.eq(3)] = 2
    out.loc[current & m.between(4, 12)] = 3
    fifth = y.eq(2024)
    out.loc[fifth & m.eq(1)] = 3
    out.loc[fifth & m.eq(2)] = 2
    out.loc[fifth & m.eq(3)] = 1
    return out


def calendar_value(frame: pd.DataFrame, stem: str) -> pd.Series:
    cq = pd.to_numeric(frame[f"{stem}CQ"], errors="coerce").fillna(0)
    pq = pd.to_numeric(frame[f"{stem}PQ"], errors="coerce").fillna(0)
    year = pd.to_numeric(frame["QINTRVYR"], errors="coerce")
    month = pd.to_numeric(frame["QINTRVMO"], errors="coerce")
    out = pd.Series(0.0, index=frame.index)
    mask = year.eq(2023) & month.between(1, 3)
    out.loc[mask] = cq.loc[mask]
    mask = year.eq(2023) & month.between(4, 12)
    out.loc[mask] = cq.loc[mask] + pq.loc[mask]
    mask = year.eq(2024) & month.between(1, 3)
    out.loc[mask] = pq.loc[mask]
    return out


def load_interview(zip22: Path, zip23: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    fmli_members = [
        (zip22, "intrvw22/fmli231.csv"),
        (zip23, "intrvw23/fmli232.csv"),
        (zip23, "intrvw23/fmli233.csv"),
        (zip23, "intrvw23/fmli234.csv"),
        (zip23, "intrvw23/fmli241.csv"),
    ]
    base = [
        "NEWID", "AGE_REF", "FAM_SIZE", "NO_EARNR", "CUTENURE",
        "FINLWT21", "QINTRVYR", "QINTRVMO", "FINATXEM",
        "TOTEXPCQ", "TOTEXPPQ", "FOODCQ", "FOODPQ",
        "RETPENCQ", "RETPENPQ",
    ] + REPLICATES
    fmli = pd.concat(
        [read_member(path, member, base) for path, member in fmli_members],
        ignore_index=True,
    )
    fmli["NEWID_STR"] = normalize_newid(fmli["NEWID"])
    fmli["MO_SCOPE"] = scope_months(fmli["QINTRVYR"], fmli["QINTRVMO"])
    fmli = fmli.loc[fmli["MO_SCOPE"].gt(0)].copy()
    fmli["HOUSING_GROUP"] = pd.to_numeric(fmli["CUTENURE"], errors="coerce").map(TENURE)
    fmli["TOTEXP_CY"] = calendar_value(fmli, "TOTEXP")
    fmli["FOOD_CY"] = calendar_value(fmli, "FOOD")
    fmli["RETPEN_CY"] = calendar_value(fmli, "RETPEN")

    mtbi_frames = []
    pattern = re.compile(r"mtbi(231|232|233|234|241)\.csv$", re.IGNORECASE)
    for path in (zip22, zip23):
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if pattern.search(member):
                    mtbi_frames.append(
                        read_member(
                            path,
                            member,
                            ["NEWID", "REF_YR", "UCC", "COST", "PUBFLAG"],
                        )
                    )
    mtbi = pd.concat(mtbi_frames, ignore_index=True)
    mtbi["NEWID_STR"] = normalize_newid(mtbi["NEWID"])
    mtbi["UCC6"] = (
        pd.to_numeric(mtbi["UCC"], errors="coerce")
        .astype("Int64").astype(str).str.zfill(6)
    )
    mtbi = mtbi.loc[
        pd.to_numeric(mtbi["REF_YR"], errors="coerce").eq(2023)
        & pd.to_numeric(mtbi["PUBFLAG"], errors="coerce").eq(2)
    ].copy()
    return fmli, mtbi


def load_diary(zip23: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    fmld_cols = [
        "NEWID", "AGE_REF", "FAM_SIZE", "NO_EARNR", "CUTENURE",
        "FINLWT21", "FOODTOT", "FOODHOME", "FOODAWAY",
    ] + REPLICATES
    fmld = pd.concat(
        [
            read_member(zip23, f"diary23/fmld23{quarter}.csv", fmld_cols)
            for quarter in range(1, 5)
        ],
        ignore_index=True,
    )
    fmld["NEWID_STR"] = normalize_newid(fmld["NEWID"])
    fmld["CUID"] = fmld["NEWID_STR"].str[:-1]
    fmld["HOUSING_GROUP"] = pd.to_numeric(fmld["CUTENURE"], errors="coerce").map(TENURE)

    expd = pd.concat(
        [
            read_member(
                zip23,
                f"diary23/expd23{quarter}.csv",
                ["NEWID", "UCC", "COST", "PUB_FLAG"],
            )
            for quarter in range(1, 5)
        ],
        ignore_index=True,
    )
    expd["NEWID_STR"] = normalize_newid(expd["NEWID"])
    expd["UCC6"] = (
        pd.to_numeric(expd["UCC"], errors="coerce")
        .astype("Int64").astype(str).str.zfill(6)
    )
    expd = expd.loc[pd.to_numeric(expd["PUB_FLAG"], errors="coerce").eq(2)].copy()
    return fmld, expd


def load_diary_summary(zip_path: Path, year: int) -> pd.DataFrame:
    """Load FMLD weekly summary records for one calendar year."""
    yy = str(year)[-2:]
    columns = [
        "NEWID", "AGE_REF", "FAM_SIZE", "NO_EARNR", "CUTENURE",
        "FINLWT21", "FOODTOT", "FOODHOME", "FOODAWAY",
    ] + REPLICATES
    frame = pd.concat(
        [
            read_member(zip_path, f"diary{yy}/fmld{yy}{quarter}.csv", columns)
            for quarter in range(1, 5)
        ],
        ignore_index=True,
    )
    frame["NEWID_STR"] = normalize_newid(frame["NEWID"])
    frame["CUID"] = frame["NEWID_STR"].str[:-1]
    frame["HOUSING_GROUP"] = pd.to_numeric(
        frame["CUTENURE"], errors="coerce"
    ).map(TENURE)
    return frame


def selected_diary_home_uccs(expd: pd.DataFrame) -> set[str]:
    prefix = pd.to_numeric(expd["UCC6"].str[:2], errors="coerce")
    selected = set(expd.loc[prefix.between(1, 18), "UCC6"].unique())
    if len(selected) < 60:
        raise ValidationError(f"Unexpected Diary food-at-home UCC set: {len(selected)}")
    return selected


def attach_ucc_sum(
    family: pd.DataFrame,
    detail: pd.DataFrame,
    uccs: set[str],
    output: str,
) -> None:
    totals = (
        detail.loc[detail["UCC6"].isin(uccs)]
        .groupby("NEWID_STR", observed=True)["COST"]
        .sum()
    )
    family[output] = family["NEWID_STR"].map(totals).fillna(0.0)


def interview_population(frame: pd.DataFrame, weight: str = "FINLWT21") -> float:
    w = pd.to_numeric(frame[weight], errors="coerce").fillna(0)
    return float((w / 4 * frame["MO_SCOPE"] / 3).sum())


def diary_population(frame: pd.DataFrame, weight: str = "FINLWT21") -> float:
    w = pd.to_numeric(frame[weight], errors="coerce").fillna(0)
    return float((w / 4).sum())


def interview_mean(frame: pd.DataFrame, column: str, weight: str = "FINLWT21") -> float:
    x = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    w = pd.to_numeric(frame[weight], errors="coerce").fillna(0)
    denominator = interview_population(frame, weight)
    return float((x * w).sum() / denominator)


def diary_mean(frame: pd.DataFrame, column: str, weight: str = "FINLWT21") -> float:
    x = pd.to_numeric(frame[column], errors="coerce").fillna(0)
    w = pd.to_numeric(frame[weight], errors="coerce").fillna(0)
    denominator = diary_population(frame, weight)
    if not math.isfinite(denominator) or denominator <= 0:
        return math.nan
    return float((x * 52 * w / 4).sum() / denominator)


def annual_income_mean(frame: pd.DataFrame, column: str, weight: str = "FINLWT21") -> float:
    x = pd.to_numeric(frame[column], errors="coerce")
    w = pd.to_numeric(frame[weight], errors="coerce")
    scoped_weight = w / 4 * frame["MO_SCOPE"] / 3
    mask = x.notna() & scoped_weight.gt(0)
    return float((x.loc[mask] * scoped_weight.loc[mask]).sum() / scoped_weight.loc[mask].sum())


def brr(frame: pd.DataFrame, column: str, survey: str) -> float:
    mean_fn = interview_mean if survey == "interview" else diary_mean
    full = mean_fn(frame, column)
    estimates = np.asarray([mean_fn(frame, column, rep) for rep in REPLICATES])
    if not np.isfinite(estimates).all():
        return math.nan
    return float(np.sqrt(np.mean((estimates - full) ** 2)))


def group_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    age = pd.to_numeric(frame["AGE_REF"], errors="coerce").between(25, 34)
    one = pd.to_numeric(frame["FAM_SIZE"], errors="coerce").eq(1)
    earner = pd.to_numeric(frame["NO_EARNR"], errors="coerce").ge(1)
    benchmark = age & one
    y1 = benchmark & earner
    return {
        "all_consumer_units": pd.Series(True, index=frame.index),
        "benchmark_all_one_person_25_34": benchmark,
        "y1_all": y1,
        "y1_renter": y1 & frame["HOUSING_GROUP"].eq("renter"),
        "y1_owner_with_mortgage": y1 & frame["HOUSING_GROUP"].eq("owner_with_mortgage"),
        "y1_owner_without_mortgage": y1 & frame["HOUSING_GROUP"].eq("owner_without_mortgage"),
        "y1_no_cash_rent": y1 & frame["HOUSING_GROUP"].eq("no_cash_rent"),
    }


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = [
        validate_zip(args.interview_2022),
        validate_zip(args.interview_2023),
        validate_zip(args.diary_2022),
        validate_zip(args.diary_2023),
    ]
    (args.output_dir / "issue-01-round-09-source-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    interview, mtbi = load_interview(args.interview_2022, args.interview_2023)
    diary, expd = load_diary(args.diary_2023)
    diary_home = selected_diary_home_uccs(expd)

    attach_ucc_sum(interview, mtbi, INTERVIEW_HOME, "I_HOME_SELECTED")
    attach_ucc_sum(interview, mtbi, INTERVIEW_AWAY, "I_AWAY_SELECTED")
    interview["I_FOOD_SELECTED"] = interview["I_HOME_SELECTED"] + interview["I_AWAY_SELECTED"]
    interview["I_RETAINED_TOTAL"] = (
        interview["TOTEXP_CY"] - interview["FOOD_CY"] + interview["I_FOOD_SELECTED"]
    )

    attach_ucc_sum(diary, expd, diary_home, "D_HOME_SELECTED")
    attach_ucc_sum(diary, expd, DIARY_AWAY, "D_AWAY_SELECTED")
    diary["D_FOOD_SELECTED"] = diary["D_HOME_SELECTED"] + diary["D_AWAY_SELECTED"]

    interview_masks = group_masks(interview)
    diary_masks = group_masks(diary)
    estimate_rows = []
    sample_rows = []
    accounting_rows = []

    definitions = [
        ("food_at_home", "I_HOME_SELECTED", "D_HOME_SELECTED", "integrated_food_validated"),
        ("food_away_from_home", "I_AWAY_SELECTED", "D_AWAY_SELECTED", "integrated_food_validated"),
        ("food_total_integrated", "I_FOOD_SELECTED", "D_FOOD_SELECTED", "integrated_food_validated"),
        (
            "partial_integrated_total_expenditure",
            "I_RETAINED_TOTAL",
            "D_FOOD_SELECTED",
            "partial_integration_nonfood_interview_only",
        ),
    ]

    for group in interview_masks:
        int_group = interview.loc[interview_masks[group]].copy()
        dia_group = diary.loc[diary_masks[group]].copy()
        sample_rows.append(
            {
                "group": group,
                "interview_records": len(int_group),
                "interview_unique_cu": int_group["NEWID_STR"].str[:-1].nunique(),
                "interview_population": interview_population(int_group),
                "diary_week_records": len(dia_group),
                "diary_unique_cu": dia_group["CUID"].nunique(),
                "diary_population": diary_population(dia_group),
            }
        )

        group_estimates = {}
        for measure, int_col, dia_col, status in definitions:
            int_mean = interview_mean(int_group, int_col)
            int_se = brr(int_group, int_col, "interview")
            dia_mean = diary_mean(dia_group, dia_col)
            dia_se = brr(dia_group, dia_col, "diary")
            combined = int_mean + dia_mean
            combined_se = (
                math.sqrt(int_se**2 + dia_se**2)
                if math.isfinite(int_se) and math.isfinite(dia_se)
                else math.nan
            )
            group_estimates[measure] = combined
            estimate_rows.append(
                {
                    "group": group,
                    "measure": measure,
                    "interview_component_mean": int_mean,
                    "interview_component_se": int_se,
                    "diary_component_mean": dia_mean,
                    "diary_component_se": dia_se,
                    "combined_mean": combined,
                    "combined_se": combined_se,
                    "rse_pct": 100 * combined_se / abs(combined)
                    if combined and math.isfinite(combined_se)
                    else math.nan,
                    "ci95_low": combined - 1.96 * combined_se
                    if math.isfinite(combined_se)
                    else math.nan,
                    "ci95_high": combined + 1.96 * combined_se
                    if math.isfinite(combined_se)
                    else math.nan,
                    "status": status,
                }
            )

        if group != "all_consumer_units":
            after_tax = annual_income_mean(int_group, "FINATXEM")
            retirement = interview_mean(int_group, "RETPEN_CY")
            partial_total = group_estimates["partial_integrated_total_expenditure"]
            accounting_rows.append(
                {
                    "group": group,
                    "income_after_tax_mean": after_tax,
                    "integrated_food_mean": group_estimates["food_total_integrated"],
                    "partial_integrated_total_expenditure_mean": partial_total,
                    "group_mean_difference_after_tax_minus_partial_total": after_tax - partial_total,
                    "retirement_pension_social_security_mean": retirement,
                    "classification_sensitivity_difference_excluding_retirement":
                        after_tax - (partial_total - retirement),
                    "status": "accounting_sensitivity_not_individual_cash_flow",
                    "warning": (
                        "Partial total retains Interview-only nonfood categories and cannot "
                        "support individual residual distributions."
                    ),
                }
            )

    estimates = pd.DataFrame(estimate_rows)
    estimates.to_csv(
        args.output_dir / "issue-01-round-09-integrated-food-estimates.csv",
        index=False,
    )
    pd.DataFrame(sample_rows).to_csv(
        args.output_dir / "issue-01-round-09-sample-audit.csv",
        index=False,
    )
    pd.DataFrame(accounting_rows).to_csv(
        args.output_dir / "issue-01-round-09-group-accounting.csv",
        index=False,
    )

    all_cu = estimates.loc[estimates["group"].eq("all_consumer_units")].set_index("measure")
    validation_rows = []
    for measure, official in [
        ("food_at_home", OFFICIAL_2023["food_at_home"]),
        ("food_away_from_home", OFFICIAL_2023["food_away_from_home"]),
        ("food_total_integrated", OFFICIAL_2023["food_total_integrated"]),
        ("partial_integrated_total_expenditure", OFFICIAL_2023["total_expenditure"]),
    ]:
        estimate = float(all_cu.loc[measure, "combined_mean"])
        percent_difference = 100 * (estimate / official - 1)
        food_measure = measure.startswith("food_")
        status = (
            "pass"
            if food_measure and abs(percent_difference) <= args.validation_tolerance_pct
            else "expected_block"
            if not food_measure
            else "fail"
        )
        validation_rows.append(
            {
                "measure": measure,
                "pumd_estimate": estimate,
                "official_2023_value": official,
                "absolute_difference": estimate - official,
                "percent_difference": percent_difference,
                "validation_threshold_pct": args.validation_tolerance_pct
                if food_measure
                else math.nan,
                "status": status,
            }
        )
    validation = pd.DataFrame(validation_rows)
    validation.to_csv(args.output_dir / "issue-01-round-09-validation.csv", index=False)

    # Diary-only year sensitivity. The 2022 Diary package is not needed to
    # construct the primary 2023 calendar estimate, but provides a useful
    # adjacent-year diagnostic for small demographic cells.
    diary_2022 = load_diary_summary(args.diary_2022, 2022)
    sensitivity_rows = []
    for year, diary_year in [(2022, diary_2022), (2023, diary)]:
        masks = group_masks(diary_year)
        for group in [
            "benchmark_all_one_person_25_34",
            "y1_all",
            "y1_renter",
            "y1_owner_with_mortgage",
        ]:
            subset = diary_year.loc[masks[group]]
            for column in ["FOODHOME", "FOODAWAY", "FOODTOT"]:
                sensitivity_rows.append(
                    {
                        "year": year,
                        "group": group,
                        "measure": column.lower(),
                        "weekly_records": len(subset),
                        "unique_cu": subset["CUID"].nunique(),
                        "weighted_population": diary_population(subset),
                        "annual_mean": diary_mean(subset, column),
                        "brr_se": brr(subset, column, "diary"),
                    }
                )
    pd.DataFrame(sensitivity_rows).to_csv(
        args.output_dir / "issue-01-round-09-diary-year-sensitivity.csv",
        index=False,
    )

    failed = validation.loc[
        validation["measure"].str.startswith("food_") & validation["status"].ne("pass")
    ]
    if not failed.empty:
        raise ValidationError(
            "Food integration did not reproduce official 2023 values:\n"
            + failed.to_string(index=False)
        )

    component_rows = []
    for survey, category, uccs, family, detail, mean_fn, se_survey in [
        ("Interview", "food_home", INTERVIEW_HOME, interview, mtbi, interview_mean, "interview"),
        ("Interview", "food_away", INTERVIEW_AWAY, interview, mtbi, interview_mean, "interview"),
        ("Diary", "food_home", diary_home, diary, expd, diary_mean, "diary"),
        ("Diary", "food_away", DIARY_AWAY, diary, expd, diary_mean, "diary"),
    ]:
        for ucc in sorted(uccs):
            column = "_TEMP_UCC"
            attach_ucc_sum(family, detail, {ucc}, column)
            component_rows.append(
                {
                    "survey": survey,
                    "category": category,
                    "ucc": ucc,
                    "annual_mean": mean_fn(family, column),
                    "brr_se": brr(family, column, se_survey),
                }
            )
    pd.DataFrame(component_rows).to_csv(
        args.output_dir / "issue-01-round-09-ucc-components-all-cu.csv",
        index=False,
    )

    print(validation.to_string(index=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        raise SystemExit(f"VALIDATION FAILED: {exc}") from exc
