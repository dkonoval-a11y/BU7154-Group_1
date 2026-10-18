#!/usr/bin/env python3
"""Rebuild the BU7141 data pipeline from raw customer records, offline.

    python run.py
    python -m unittest discover -s tests -v

Reference workbooks are only read by the final comparison stage. Calculations
run independently from inputs/raw.xlsx; --skip-reference-checks demonstrates
that the Excel result files are not computational inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from src.analysis import (CUTOFF, GROUP_A, GROUP_B, START, STOP, age_results,
                          annual, descriptive_results, monthly, prepare,
                          retention_results, seasonal)
from src.database import build_database
from src.validation import monthly_diagnostics, source_checks, verify_references

ROOT = Path(__file__).resolve().parent


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_json(x):
    if isinstance(x,dict):return {str(k):clean_json(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [clean_json(v) for v in x]
    if isinstance(x,(pd.Timestamp,)):return x.isoformat()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,float) and not np.isfinite(x):return None
    return x


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(clean_json(data),indent=2,ensure_ascii=False),encoding="utf-8")


def write_tables(out: Path, tables: dict[str,pd.DataFrame]) -> None:
    out.mkdir(parents=True,exist_ok=True)
    for name,frame in tables.items():
        frame.to_csv(out/f"{name}.csv",index=False,float_format="%.17g",
                     date_format="%Y-%m-%dT%H:%M:%S.%f",encoding="utf-8-sig")


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw",type=Path,default=ROOT/"inputs/raw.xlsx")
    ap.add_argument("--references",type=Path,default=ROOT/"reference")
    ap.add_argument("--output",type=Path,default=ROOT/"outputs")
    ap.add_argument("--skip-reference-checks",action="store_true",
                    help="Calculate from raw only; explicitly leave reference matching unverified.")
    args=ap.parse_args(argv)
    if not args.raw.is_file():ap.error(f"Missing raw workbook: {args.raw}")
    refs=["BU7141_Data_Transformation.xlsx","Monthly_Membership_Results.xlsx",
          "Age_Group_Results.xlsx","Retention_Results.xlsx"]
    if not args.skip_reference_checks:
        missing=[str(args.references/f) for f in refs if not (args.references/f).is_file()]
        if missing:ap.error("Missing reference workbooks. Restore them or use --skip-reference-checks: "+", ".join(missing))
    args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/"validation_report.json",{"status":"IN_PROGRESS",
               "note":"The latest run has not completed. A previous PASS is not current."})
    (args.output/"VALIDATION.md").write_text("# Validation not complete\n\nThe latest run has not completed.\n",encoding="utf-8")
    print("1/5 Read raw source; prepare customer-level data.",flush=True)
    raw=pd.read_excel(args.raw,sheet_name="DadosV3")
    raw=raw.loc[:,~raw.columns.astype(str).str.startswith("Unnamed:")]
    master,d=prepare(raw)
    checks=source_checks(d)
    failed=checks[checks.Result.eq("FAIL")]
    if len(failed):
        write_tables(args.output/"validation",{"SourceChecks":checks})
        raise ValueError("Source validation failed: "+", ".join(failed.Check))
    print("2/5 Calculate monthly, age-group and fixed-day retention tables.",flush=True)
    m=monthly(d)
    monthly_tables={"MonthlyData":m,"SeasonalSummary":seasonal(m),"AnnualSummary":annual(m),
                    **monthly_diagnostics(d,m)}
    age_tables=age_results(d)
    retention_tables=retention_results(d)
    descriptive=descriptive_results(d)
    residuals=monthly_tables["MonthlyReconciliation"].drop(columns="MonthStart")
    if residuals.abs().max().max()>1e-12:
        raise ValueError("Monthly stock/flow reconciliation failed")
    if not np.array_equal(m.OpeningMemberships.iloc[1:],m.ActiveMemberships.iloc[:-1]):
        raise ValueError("Opening/closing continuity failed")
    for col in ("AnnualEnrolmentShare","AnnualDropoutShare"):
        if not np.allclose(m.groupby("Year")[col].sum(),1):
            raise ValueError(f"Annual shares do not sum to one: {col}")
    print("3/5 Export CSV tables and build the four-table SQLite database.",flush=True)
    write_tables(args.output/"data",{"RawSource":raw,"AnalysisData":master,
                 "EntryAgeCalculations":d[["Id","StartDate","FinishDate","AgeReferenceDate",
                                            "Age","EntryAgeLower","EstimatedEntryAge","EntryAgeUpper","ValidAge"]]})
    write_tables(args.output/"monthly",monthly_tables)
    write_tables(args.output/"age_groups",age_tables)
    write_tables(args.output/"retention",retention_tables)
    write_tables(args.output/"descriptive",descriptive)
    write_tables(args.output/"validation",{"SourceChecks":checks})
    db=build_database(d,args.output/"database",ROOT/"schema.sql")
    print("4/5 Compare every reconstructed reference-table cell.",flush=True)
    if args.skip_reference_checks:
        comparison=pd.DataFrame(columns=["Table","Status","Rows","CellsCompared","NumericCellsCompared","Mismatches","Detail"])
        details=pd.DataFrame(columns=["Table","Row","Column","Actual","Expected"])
        status="NOT_RUN"
    else:
        comparison,details=verify_references(args.references,master,monthly_tables,age_tables,retention_tables,checks)
        status="PASS" if comparison.Status.eq("PASS").all() else "FAIL"
    write_tables(args.output/"validation",{"ReferenceComparison":comparison,"CellMismatches":details})
    provenance={"raw_file":args.raw.name,"raw_sha256":file_hash(args.raw),
                "reference_workbooks":{f:file_hash(args.references/f) for f in refs if (args.references/f).is_file()},
                "calculation_input":"Raw workbook only. Reference values are never read by calculation functions.",
                "code_origin":"Independent reconstruction with Codex; not the original team Python notebooks.",
                "observation_cutoff":CUTOFF,"reporting_start":START,"reporting_stop_exclusive":STOP,
                "recorded_age_activity_scope":"Full source history; original recorded age.",
                "estimated_entry_age_scope":"A: 18 <= estimate < 25; B: estimate >= 35.",
                "numeric_tolerance":{"absolute":1e-10,"relative":1e-12},
                "python_version":sys.version.split()[0],"pandas_version":pd.__version__,"numpy_version":np.__version__}
    write_json(args.output/"provenance.json",provenance)
    summary={"status":status,"source_rows":len(raw),"source_fields":len(raw.columns),
             "analysis_columns":len(master.columns),"reference_sections":len(comparison),
             "cells_compared":int(comparison.CellsCompared.sum()),
             "numeric_cells_compared":int(comparison.NumericCellsCompared.sum()),
             "mismatches":int(comparison.Mismatches.sum()),"database":db,
             "annual_summary":monthly_tables["AnnualSummary"].to_dict("records"),
             "retention_all_2015_2018":retention_tables["Summary"].query("Scope == 'All 2015-2018'").to_dict("records"),
             "scope_note":"Source preparation and analytical values are reproduced; original Excel layout, formula strings and explanatory prose are not regenerated."}
    write_json(args.output/"validation_report.json",summary)
    lines=["# Reconstruction validation", "",f"Reference comparison: **{status}**.","",
           f"Source customers: {len(raw):,}. Compared cells: {summary['cells_compared']:,}. Mismatches: {summary['mismatches']}.","",
           "| Section | Rows | Cells | Mismatches | Status |","|---|---:|---:|---:|---|"]
    lines.extend(f"| {r.Table} | {r.Rows} | {r.CellsCompared} | {r.Mismatches} | {r.Status} |" for r in comparison.itertuples())
    lines.extend(["","Floating-point comparisons allow absolute 1e-10 and relative 1e-12 rounding differences.",
                  "The original reference files are retained unchanged. Original source code was unavailable.",
                  "See SourceChecks.csv for preserved source-data anomalies; these were not silently corrected."])
    (args.output/"VALIDATION.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"5/5 Finished. Status={status}; cells={summary['cells_compared']:,}; mismatches={summary['mismatches']}.",flush=True)
    print(f"Output: {args.output.resolve()}",flush=True)
    return 0 if status in ("PASS","NOT_RUN") else 1


if __name__=="__main__":
    raise SystemExit(main())
