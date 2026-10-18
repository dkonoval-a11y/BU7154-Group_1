# Sources and attribution

## Original public customer dataset

Pinheiro, P., & Cavique, L. (2020). *Sport Services Dataset* (Version 1) [Data set].
Mendeley Data. https://doi.org/10.17632/yprk4jdgnv.1

Public dataset page: https://data.mendeley.com/datasets/yprk4jdgnv/1

The public dataset page identifies the licence as CC BY 4.0. The bundled raw
Excel file is the version uploaded by the user, preserved without alteration
and renamed to `inputs/raw.xlsx` for portable execution. Its SHA-256 fingerprint
is recorded in outputs/provenance.json. File format identity with an unprovided
repository download is not assumed.

Pinheiro, P., & Cavique, L. (2021). Regular sports services: Dataset of
demographic, frequency and service level agreement. *Data in Brief, 36*,
Article 107054. https://doi.org/10.1016/j.dib.2021.107054

Accessible paper:
https://repositorioaberto.uab.pt/server/api/core/bitstreams/d6a0f00e-1bac-4e0e-80d6-2f4e7dde7e6a/content

## Supplied preparation and analytical references

- `BU7141_Data_Transformation.xlsx`: supplied project preparation workbook,
  including AnalysisData, DataDictionary and the unfilled revenue input template.
- Wang, Y. (2026a). *Age group results* [Unpublished project workbook,
  Age_Group_Results.xlsx].
- Wang, Y. (2026b). *Monthly membership results* [Unpublished project workbook,
  Monthly_Membership_Results.xlsx].
- Wang, Y. (2026c). *Retention results* [Unpublished project workbook,
  Retention_Results.xlsx].
- Updated conceptual and logical ERD diagrams supplied by the project group.
  The original diagrams.net XML is preserved in reference/Conceptual_ERD.drawio
  and reference/Logical_ERD.drawio.

The three analytical workbooks are outputs from one customer dataset, not three
independent datasets. No public repository URL for the original team code was
supplied, and no such URL has been invented here.

## This reconstruction

The executable code, validation framework and SQLite implementation were newly
created with Codex on 18 October 2026. The project reproduces the team's
documented calculations and checks their values, while preserving attribution
to the original dataset authors and to the team analysis. It is not a claim
that these are Yinran's original Python notebooks or that a SQLite database was
used in the team's previous analysis.

When adding this to a shared repository, describe that distinction in the
repository history and report references. This package performs no publication
or GitHub mutation automatically.
