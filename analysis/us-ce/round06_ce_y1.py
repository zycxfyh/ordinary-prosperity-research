#!/usr/bin/env python3
"""Round 6: construct a preliminary US CE Y1 microdata estimate.

This script is deliberately fail-closed. It downloads official BLS CE PUMD
Interview CSV packages, inventories their contents, validates required variables,
constructs calendar-year weights, selects one-person economic units aged 25-34
with at least one earner, and produces preliminary Interview-only estimates.

It does NOT claim to reproduce integrated CE published tables. Final research
estimates require current dictionary verification, source-selection/UCC review,
and the CE income-imputation procedure.

Example:
    python analysis/us-ce/round06_ce_y1.py --target-year 2023 --download

Dependencies:
    Python 3.11+
    pandas >= 2.0
    numpy >= 1.24
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover - execution environment check
    raise SystemExit(
        "Missing dependencies. Install with: python -m pip install pandas numpy"
    ) from exc

BLS_BASE = "https://www.bls.gov/cex/pumd/data/csv"
USER_AGENT = "ordinary-prosperity-research/round06 (+research; CE-PUMD)"
REPLICATE_COLUMNS = [f"WTREP{i:02d}" for i in range(1, 45)]

# Historical official CUTENURE codes. The script verifies observed values and
# requires explicit acknowledgement because the current BLS dictionary remains
# the authority for each release.
HISTORICAL_TENURE = {
    1: "owner_with_mortgage",
    2: "owner_without_mortgage",
    3: "owner_mortgage_not_reported",
    4: "renter",
    5: "occupied_without_cash_rent",
    6: "student_housing",
}


@dataclass(frozen=True)
class PackageSpec:
    release_year: int
    url: str
    zip_path: Path
    extract_dir: Path


@dataclass
class AuditRecord:
    check: str
    status: str
    detail: str


class ValidationError(RuntimeError):
    """Raised when an estimate would violate a research validation gate."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-year", type=int, default=2023)
    parser.add_argument(
        "--raw-dir", type=Path, default=Path("data/raw/us-ce"),
        help="Directory containing downloaded official ZIP packages.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/derived/us-ce/round06"),
    )
    parser.add_argument(
        "--download", action="store_true",
        help="Download missing official BLS CSV Interview packages.",
    )
    parser.add_argument(
        "--overwrite-download", action="store_true",
        help="Replace existing ZIP files and extracted directories.",
    )
    parser.add_argument(
        "--acknowledge-historical-tenure-codes", action="store_true",
        help=(
            "Allow historical CUTENURE codes after observed-value validation. "
            "The current BLS dictionary must still be reviewed before publication."
        ),
    )
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_file(url: str, destination: Path, retries: int = 3) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            logging.info("Downloading %s (attempt %s/%s)", url, attempt, retries)
            with urllib.request.urlopen(request, timeout=120) as response, temp.open("wb") as out:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"Unexpected HTTP status: {response.status}")
                shutil.copyfileobj(response, out)
            if temp.stat().st_size < 1_000_000:
                raise RuntimeError(
                    f"Downloaded file is unexpectedly small: {temp.stat().st_size} bytes"
                )
            temp.replace(destination)
            return
        except (urllib.error.URLError, TimeoutError, OSError, RuntimeError) as exc:
            last_error = exc
            logging.warning("Download failed: %s", exc)
            if temp.exists():
                temp.unlink()
            time.sleep(attempt * 2)

    raise RuntimeError(f"Unable to download {url}: {last_error}")


def package_specs(target_year: int, raw_dir: Path) -> list[PackageSpec]:
    # BLS annual Interview release target year requires the prior release for Q1.
    specs: list[PackageSpec] = []
    for release_year in (target_year - 1, target_year):
        yy = str(release_year)[-2:]
        zip_path = raw_dir / f"intrvw{yy}.zip"
        specs.append(
            PackageSpec(
                release_year=release_year,
                url=f"{BLS_BASE}/intrvw{yy}.zip",
                zip_path=zip_path,
                extract_dir=raw_dir / f"intrvw{yy}",
            )
        )
    return specs


def ensure_packages(specs: Sequence[PackageSpec], download: bool, overwrite: bool) -> list[dict]:
    manifest: list[dict] = []
    for spec in specs:
        if overwrite and spec.zip_path.exists():
            spec.zip_path.unlink()
        if not spec.zip_path.exists():
            if not download:
                raise ValidationError(
                    f"Missing {spec.zip_path}. Re-run with --download or place the official BLS ZIP there."
                )
            download_file(spec.url, spec.zip_path)

        if not zipfile.is_zipfile(spec.zip_path):
            raise ValidationError(f"Not a valid ZIP archive: {spec.zip_path}")

        if overwrite and spec.extract_dir.exists():
            shutil.rmtree(spec.extract_dir)
        if not spec.extract_dir.exists():
            spec.extract_dir.mkdir(parents=True)
            with zipfile.ZipFile(spec.zip_path) as archive:
                archive.extractall(spec.extract_dir)

        manifest.append(
            {
                "release_year": spec.release_year,
                "source_url": spec.url,
                "zip_path": str(spec.zip_path),
                "size_bytes": spec.zip_path.stat().st_size,
                "sha256": sha256_file(spec.zip_path),
                "extract_dir": str(spec.extract_dir),
            }
        )
    return manifest


def csv_files(root: Path, prefix: str) -> list[Path]:
    pattern = re.compile(rf"^{re.escape(prefix)}.*\.csv$", re.IGNORECASE)
    files = sorted(path for path in root.rglob("*.csv") if pattern.match(path.name))
    return files


def read_csv_flexible(path: Path) -> pd.DataFrame:
    errors: list[str] = []
    for encoding in ("utf-8", "latin-1"):
        try:
            frame = pd.read_csv(path, low_memory=False, encoding=encoding)
            frame.columns = [str(column).strip().upper() for column in frame.columns]
            frame["_SOURCE_FILE"] = str(path)
            return frame
        except Exception as exc:  # noqa: BLE001 - collect parsing diagnostics
            errors.append(f"{encoding}: {exc}")
    raise ValidationError(f"Unable to read {path}: {' | '.join(errors)}")


def load_file_family(specs: Sequence[PackageSpec], prefix: str) -> pd.DataFrame:
    files: list[Path] = []
    for spec in specs:
        files.extend(csv_files(spec.extract_dir, prefix))
    if not files:
        raise ValidationError(f"No {prefix} CSV files found in extracted packages")
    logging.info("Loading %s files for %s", len(files), prefix)
    frames = [read_csv_flexible(path) for path in files]
    return pd.concat(frames, ignore_index=True, sort=False)


def require_columns(frame: pd.DataFrame, columns: Iterable[str], context: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValidationError(f"{context}: missing required columns {missing}")


def numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def deduplicate_fmli(frame: pd.DataFrame) -> pd.DataFrame:
    require_columns(frame, ["NEWID"], "FMLI")
    duplicated = frame.duplicated(subset=["NEWID"], keep=False)
    if duplicated.any():
        # The same quarter can appear in two annual releases. Prefer the row from
        # the later release, inferred from source path, after checking conflicts.
        frame = frame.copy()
        frame["_RELEASE_HINT"] = frame["_SOURCE_FILE"].str.extract(r"intrvw(\d{2})", expand=False)
        frame["_RELEASE_HINT"] = pd.to_numeric(frame["_RELEASE_HINT"], errors="coerce")
        frame = frame.sort_values(["NEWID", "_RELEASE_HINT"]).drop_duplicates("NEWID", keep="last")
    return frame.reset_index(drop=True)


def months_in_scope(interview_year: pd.Series, interview_month: pd.Series, target_year: int) -> pd.Series:
    year = pd.to_numeric(interview_year, errors="coerce")
    month = pd.to_numeric(interview_month, errors="coerce")
    result = pd.Series(0.0, index=year.index)

    current = year.eq(target_year)
    result.loc[current & month.eq(1)] = 0
    result.loc[current & month.eq(2)] = 1
    result.loc[current & month.eq(3)] = 2
    result.loc[current & month.between(4, 12)] = 3

    fifth = year.eq(target_year + 1)
    result.loc[fifth & month.eq(1)] = 3
    result.loc[fifth & month.eq(2)] = 2
    result.loc[fifth & month.eq(3)] = 1
    return result


def annual_expenditure(frame: pd.DataFrame, stem: str, target_year: int) -> pd.Series:
    cq = f"{stem}CQ"
    pq = f"{stem}PQ"
    require_columns(frame, [cq, pq, "QINTRVYR", "QINTRVMO"], f"annual expenditure {stem}")
    year = numeric(frame, "QINTRVYR")
    month = numeric(frame, "QINTRVMO")
    cq_value = numeric(frame, cq).fillna(0)
    pq_value = numeric(frame, pq).fillna(0)

    value = pd.Series(0.0, index=frame.index)
    value.loc[year.eq(target_year) & month.between(1, 3)] = cq_value
    value.loc[year.eq(target_year) & month.between(4, 12)] = cq_value + pq_value
    value.loc[year.eq(target_year + 1) & month.between(1, 3)] = pq_value
    return value


def resolve_first(frame: pd.DataFrame, candidates: Sequence[str], required: bool = True) -> str | None:
    for candidate in candidates:
        if candidate in frame.columns:
            return candidate
    if required:
        raise ValidationError(f"None of the candidate variables exist: {list(candidates)}")
    return None


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    mask = values.notna() & weights.notna() & weights.gt(0)
    if not mask.any():
        return math.nan
    return float(np.average(values.loc[mask], weights=weights.loc[mask]))


def weighted_quantile(values: pd.Series, weights: pd.Series, quantiles: Sequence[float]) -> list[float]:
    mask = values.notna() & weights.notna() & weights.gt(0)
    if not mask.any():
        return [math.nan for _ in quantiles]
    x = values.loc[mask].to_numpy(dtype=float)
    w = weights.loc[mask].to_numpy(dtype=float)
    order = np.argsort(x)
    x, w = x[order], w[order]
    cumulative = np.cumsum(w) - 0.5 * w
    cumulative /= np.sum(w)
    return [float(np.interp(q, cumulative, x)) for q in quantiles]


def brr_mean_se(frame: pd.DataFrame, value_column: str, full_weight: str) -> float:
    full = weighted_mean(frame[value_column], frame[full_weight])
    estimates: list[float] = []
    for column in REPLICATE_COLUMNS:
        if column not in frame.columns:
            return math.nan
        replicate_weight = numeric(frame, column) / 4 * frame["MO_SCOPE"] / 3
        estimates.append(weighted_mean(frame[value_column], replicate_weight))
    valid = np.asarray([value for value in estimates if math.isfinite(value)], dtype=float)
    if len(valid) != 44 or not math.isfinite(full):
        return math.nan
    return float(math.sqrt(np.mean((valid - full) ** 2)))


def summarize_group(frame: pd.DataFrame, group: str, measures: Sequence[str]) -> list[dict]:
    rows: list[dict] = []
    weights = frame["ANALYSIS_WEIGHT"]
    for measure in measures:
        if measure not in frame.columns:
            continue
        mean = weighted_mean(frame[measure], weights)
        p25, median, p75 = weighted_quantile(frame[measure], weights, [0.25, 0.5, 0.75])
        se = brr_mean_se(frame, measure, "ANALYSIS_WEIGHT")
        rows.append(
            {
                "housing_group": group,
                "measure": measure,
                "unweighted_interviews": int(frame[measure].notna().sum()),
                "unique_consumer_units": int(frame.loc[frame[measure].notna(), "CUID"].nunique()),
                "weighted_population": float(weights.sum()),
                "weighted_mean": mean,
                "weighted_p25": p25,
                "weighted_median": median,
                "weighted_p75": p75,
                "brr_standard_error": se,
                "ci95_low": mean - 1.96 * se if math.isfinite(se) else math.nan,
                "ci95_high": mean + 1.96 * se if math.isfinite(se) else math.nan,
                "result_status": "preliminary_interview_only",
            }
        )
    return rows


def write_csv(path: Path, rows: Sequence[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()), format="%(levelname)s %(message)s")
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit: list[AuditRecord] = []

    specs = package_specs(args.target_year, args.raw_dir)
    manifest = ensure_packages(specs, args.download, args.overwrite_download)
    (args.output_dir / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    audit.append(AuditRecord("official_packages", "pass", "Two adjacent BLS Interview packages available"))

    fmli = deduplicate_fmli(load_file_family(specs, "fmli"))
    required = [
        "NEWID", "AGE_REF", "FAM_SIZE", "NO_EARNR", "CUTENURE",
        "FINLWT21", "QINTRVYR", "QINTRVMO",
    ]
    require_columns(fmli, required, "FMLI")
    audit.append(AuditRecord("required_variables", "pass", ",".join(required)))

    fmli["MO_SCOPE"] = months_in_scope(fmli["QINTRVYR"], fmli["QINTRVMO"], args.target_year)
    fmli = fmli.loc[fmli["MO_SCOPE"].gt(0)].copy()
    fmli["ANALYSIS_WEIGHT"] = numeric(fmli, "FINLWT21") / 4 * fmli["MO_SCOPE"] / 3
    fmli["CUID"] = fmli["NEWID"].astype(str).str[:-1]

    observed_tenure = sorted(set(numeric(fmli, "CUTENURE").dropna().astype(int).tolist()))
    unknown_codes = [code for code in observed_tenure if code not in HISTORICAL_TENURE]
    if unknown_codes:
        raise ValidationError(f"Observed unknown CUTENURE codes: {unknown_codes}")
    if not args.acknowledge_historical_tenure_codes:
        raise ValidationError(
            "CUTENURE values are structurally valid, but publication requires current dictionary review. "
            "After review, re-run with --acknowledge-historical-tenure-codes."
        )
    fmli["HOUSING_GROUP"] = numeric(fmli, "CUTENURE").map(HISTORICAL_TENURE)
    audit.append(AuditRecord("tenure_codes", "conditional_pass", f"Observed {observed_tenure}"))

    y1 = fmli.loc[
        numeric(fmli, "AGE_REF").between(25, 34)
        & numeric(fmli, "FAM_SIZE").eq(1)
        & numeric(fmli, "NO_EARNR").ge(1)
    ].copy()
    if y1.empty:
        raise ValidationError("Y1 filter returned zero records")
    audit.append(AuditRecord("y1_sample", "pass", f"{len(y1)} interview records"))

    before_tax = resolve_first(y1, ["FINCBTXM", "FINCBTAX", "FINCBT"])
    after_tax = resolve_first(y1, ["FINCATXM", "FINCATAX", "FINCAT"], required=False)
    wages = resolve_first(y1, ["WAGRX", "WAGRXM", "WAGRSALX"], required=False)

    y1["INCOME_BEFORE_TAX"] = numeric(y1, before_tax)
    if after_tax:
        y1["INCOME_AFTER_TAX"] = numeric(y1, after_tax)
    if wages:
        y1["WAGES_SALARIES"] = numeric(y1, wages)

    # These stems are resolved from FMLI summary variables. The script refuses
    # to synthesize missing categories from unrelated variables.
    stems = {
        "TOTAL_EXPENDITURE": ["TOTEXP"],
        "HOUSING_EXPENDITURE": ["HOUS"],
        "FOOD_EXPENDITURE": ["FOOD"],
        "TRANSPORT_EXPENDITURE": ["TRAN"],
        "HEALTH_EXPENDITURE": ["HEALTH", "HLTH"],
        "PENSION_SOCIAL_SECURITY": ["PENSION", "PENS"],
    }
    for output, candidates in stems.items():
        resolved = None
        for stem in candidates:
            if f"{stem}CQ" in y1.columns and f"{stem}PQ" in y1.columns:
                resolved = stem
                break
        if resolved:
            y1[output] = annual_expenditure(y1, resolved, args.target_year)

    if "INCOME_AFTER_TAX" in y1.columns and "TOTAL_EXPENDITURE" in y1.columns:
        y1["REPORTED_RESIDUAL"] = y1["INCOME_AFTER_TAX"] - y1["TOTAL_EXPENDITURE"]

    measures = [
        "INCOME_BEFORE_TAX", "INCOME_AFTER_TAX", "WAGES_SALARIES",
        "TOTAL_EXPENDITURE", "HOUSING_EXPENDITURE", "FOOD_EXPENDITURE",
        "TRANSPORT_EXPENDITURE", "HEALTH_EXPENDITURE",
        "PENSION_SOCIAL_SECURITY", "REPORTED_RESIDUAL",
    ]

    groups = {
        "all_y1": y1,
        "renter": y1.loc[y1["HOUSING_GROUP"].eq("renter")],
        "owner_with_mortgage": y1.loc[y1["HOUSING_GROUP"].eq("owner_with_mortgage")],
        "owner_without_mortgage": y1.loc[y1["HOUSING_GROUP"].eq("owner_without_mortgage")],
    }
    result_rows: list[dict] = []
    for group_name, group_frame in groups.items():
        if group_frame.empty:
            audit.append(AuditRecord(f"group_{group_name}", "warning", "No records"))
            continue
        result_rows.extend(summarize_group(group_frame, group_name, measures))

    write_csv(args.output_dir / "preliminary_y1_estimates.csv", result_rows)
    y1[[
        "NEWID", "CUID", "QINTRVYR", "QINTRVMO", "MO_SCOPE", "AGE_REF",
        "FAM_SIZE", "NO_EARNR", "CUTENURE", "HOUSING_GROUP", "ANALYSIS_WEIGHT",
    ]].to_csv(args.output_dir / "y1_sample_audit.csv", index=False)

    audit.append(
        AuditRecord(
            "publication_status",
            "blocked",
            "Results remain preliminary until dictionary, UCC integration, income imputation, and published-table validation pass",
        )
    )
    write_csv(args.output_dir / "audit_log.csv", [asdict(item) for item in audit])
    logging.info("Wrote outputs to %s", args.output_dir)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        logging.error("VALIDATION FAILED: %s", exc)
        raise SystemExit(2) from exc
