# BU7141 sports centre: reproducible Python reconstruction

This project rebuilds the supplied customer-level preparation, monthly and
age-group analyses, and 90/180-day retention results **from the raw customer
workbook**. It implements the team's updated four-entity ERD as a real SQLite
database and compares the calculated values against the supplied Excel results.

The analytical reference results are Yinran Wang's team outputs. The Python
implementation here is a new reconstruction made with Codex from the supplied
data and documented definitions. It is **not a recovered copy of his original
notebooks**. Do not describe it as the original code that produced those files.

## Quick start

Extract the complete ZIP, open a terminal in this folder, then run:

```bash
python -m pip install -r requirements.txt
python run.py
python -m unittest discover -s tests -v
```

On Windows, use `py` instead of `python` if that is how Python is installed.
Python 3.10 or newer is required. Processing is local and does not call any
website, API, external database or paid service. Installing dependencies needs
internet access if they are not already installed.

The package already contains a calculated `outputs/` folder. Re-running the
command rebuilds its data, SQLite database and validation evidence.

`Start_here.ipynb` provides the same steps in a notebook and displays the annual
and retention summaries. Run it from this extracted project directory in your
Python notebook environment. The command-line pipeline does not require Jupyter.

## What is included

| Path | Purpose |
|---|---|
| `inputs/raw.xlsx` | Unchanged copy of the uploaded `DOC-20260930-WA0000.xlsx`, sheet `DadosV3`. This is the calculation input. |
| `reference/` | The four supplied Excel files and the two updated ERD diagrams. Excel values are used only for comparison. |
| `src/analysis.py` | Preparation, monthly measures, age estimates, seasonality, retention and sensitivity calculations. |
| `src/validation.py` | Source checks, stock/flow reconciliation and cell-level Excel comparisons. |
| `src/database.py` and `schema.sql` | Physical implementation of the four-table logical model. |
| `tests/test_semantics.py` | Tests of boundary dates, censoring, age scope and common cohort weights. |
| `outputs/data/` | All raw fields, the 35-column AnalysisData table and an inspectable entry-age calculation table, as CSV. |
| `outputs/monthly/` | MonthlyData, SeasonalSummary, AnnualSummary and monthly validation sections. |
| `outputs/age_groups/` | Group counts, monthly/annual results, seasonal comparisons, paired rate gaps, focus windows and sensitivity sections. |
| `outputs/retention/` | Summary, CohortRetention, CohortComparisons and Sensitivity. |
| `outputs/descriptive/` | Recorded-age activity counts, variety by age/gender, renewals, usage averages and full-history monthly counts. |
| `outputs/database/sports_centre.sqlite` | Ready-to-open SQLite database. |
| `outputs/validation_report.json` and `outputs/VALIDATION.md` | Exact comparison coverage, counts, status and material boundaries. |
| `outputs/validation/CellMismatches.csv` | Every detected discrepancy. A successful run leaves this file with its header and no data rows. |
| `METHODS.md` | Formula definitions and how they map to the report. |

CSV files are calculated data exports for Python, Excel or Tableau. The original
Excel files remain unchanged in `reference/`; this project does not recreate
their formatting, cached formulas or explanatory wording.

## Demonstrate that reference results are not calculation inputs

```bash
python run.py --references missing_reference_folder --skip-reference-checks --output raw_only_outputs
```

This produces the same calculated data without opening any reference workbook.
Its validation status is `NOT_RUN`, not `PASS`, because comparison was explicitly
skipped. The normal command requires all four reference files and returns a
non-zero exit code if a comparison fails.

## Validation scope

The comparison covers every cell in the reconstructed AnalysisData table, all
numeric analytical tables in the monthly, age-group and retention workbooks,
the second tables embedded in FocusWindows and Sensitivity, and the numeric
validation blocks. Original explanatory prose, workbook formatting, input file
paths and historical source-file hash strings are not computational results and
are not regenerated.

Rows are matched using their actual keys, such as MonthStart or the combination
of CohortMonth, AgeGroup and HorizonDays. Counts, text, Boolean values and dates
are checked; floating-point results allow absolute roundoff of `1e-10` and
relative roundoff of `1e-12`. This is numerical equivalence, not a byte-for-byte
claim about Excel files or evidence that the original source code was identical.

The older screenshots alone are not an executable specification. In particular,
their recorded-age 25+ retention charts must not be substituted for the verified
estimated-entry-age 35+ results. Descriptive activity, renewal and usage exports
are recalculated directly from source fields; their coverage is separate from
the cell comparison against the three analytical workbooks.

## The database

The database has exactly four data tables:

- `Member`: 1 row per customer, with original recorded age and gender.
- `Membership`: 1 first-to-final summary per customer.
- `MembershipStatus`: 1 status/renewal/final-window usage summary per customer.
- `Activity`: 1 row per observed customer/activity combination; composite key
  `(Activity_Name, Member_ID)`.

`MemberSummary` is a view joining the three one-to-one customer tables. Foreign
keys and primary keys are enforced and checked during the build. SQLite does
not have a separate native datetime storage class; full source timestamps are
preserved as ISO strings. The logical name `Membership Status` is represented as
`MembershipStatus` for convenient SQL use.

The four-table database follows the supplied diagram. Other source fields,
including LastPeriodStart and LastPeriodFinish, are preserved in the raw and
analytical CSV exports. They have not been silently added to the team's ERD.

Example:

```python
import sqlite3
import pandas as pd

with sqlite3.connect("outputs/database/sports_centre.sqlite") as con:
    print(pd.read_sql_query("SELECT * FROM MemberSummary LIMIT 5", con))
    print(pd.read_sql_query(
        "SELECT Activity_Name, COUNT(*) AS Members FROM Activity GROUP BY Activity_Name",
        con,
    ))
```

Do not sum customer payments after joining the one-to-many Activity table:
that would repeat a multi-activity customer's payments. Use MemberSummary for
customer-level totals and Activity for activity counts.

## Boundaries

There is one observed first-to-final interval per customer, not a transaction
ledger. Intermediate breaks, individual renewal dates, individual invoices,
historical plan choices and the original ERP database cannot be recovered from
these summary fields. Recorded retention does not establish uninterrupted paid
membership, student/employment status, intervention effects or additional
revenue. The RevenueScenarios input template is retained in the reference file;
no historical revenue forecast or assumed tariff is reconstructed from it.

See `DATA_SOURCES.md` for original dataset attribution, team-file provenance and
the distinction between original analysis and this new implementation.
