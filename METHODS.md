# Measures and reconstruction choices

These definitions were reconstructed from the supplied workbooks, their
Definitions/Validation sections and the source field documentation. The
calculation functions read raw records only. The Excel files are independent
numerical references at the comparison stage.

## 1. Preserve and prepare

The source is the uploaded `DadosV3` worksheet: one customer per row. All source
fields and full source timestamps remain available in RawSource.csv. AnalysisData
preserves the 33 selected source fields in the supplied preparation workbook and
adds:

- FirstAnniversaryDate: calendar date 12 months after EnrollmentStart,
  equivalent to the supplied `EDATE(start, 12)` helper.
- ObservedTenureDays: calendar-date finish minus calendar-date start,
  equivalent to `INT(finish) - INT(start)`.

The fixed 90/180-day calculations below use calendar days directly; the
anniversary helper is not substituted for either horizon.

## 2. Time, events and membership stock

The reporting period is January 2015 to December 2018. Source customers joining
earlier are retained for opening membership counts. Follow-up may extend into
2019. Dropout=0 records ending on 31 October 2019 are administratively censored;
the cutoff is not a departure.

For month start M and next-month start N:

| Measure | Definition |
|---|---|
| OpeningMemberships | StartDate < M and no final exit before M. |
| NewEnrolments | M <= StartDate < N. First registrations, not renewals. |
| Dropouts | Dropout=1 and M <= FinishDate < N. |
| ActiveMemberships | StartDate < N and no final exit before N. |
| DropoutsFromOpening | Monthly exits whose StartDate < M. |
| SameMonthEnrolmentDropouts | Both first registration and final exit within the month. |
| EnrolmentRate | NewEnrolments / OpeningMemberships. |
| DropoutRate | DropoutsFromOpening / OpeningMemberships. |
| NetMembershipChange | ActiveMemberships - OpeningMemberships = NewEnrolments - Dropouts. |
| AnnualEnrolmentShare | Monthly registrations / registrations in the same calendar year and age group. |
| AnnualDropoutShare | Monthly exits / exits in the same calendar year and age group. |

The end-date convention applies an exit on its recorded calendar date. A person
exiting on the first day is in the opening population; a person exiting on the
last day is removed by the close. The source contains no complete history of
intermediate gaps, so these are reconstructed stocks within the observed cohort.

Each year receives equal weight in the four-year seasonal mean. A pooled rate
instead divides summed numerators by summed opening memberships. The code
exports these as different measures. A summed four-year percentage is not used.
Ranks use minimum competition rank for tied values.

## 3. Entry-age groups

ReferenceDate = final exit date for Dropout=1; otherwise 31 October 2019.

```text
elapsed_years = (ReferenceDate - first_registration_date).days / 365.2425
lower_entry_age = recorded_Age - elapsed_years
midpoint_entry_age = lower_entry_age + 0.5
upper_entry_age = lower_entry_age + 1.0
```

Group A uses 18 <= midpoint < 25. Group B uses midpoint >= 35. Valid source ages
are integers between 1 and 100, with a non-negative estimated entry age. Age zero
is excluded from age comparisons, not from overall customer counts. Other ages
outside A and B are outside the selected comparison, not invalid records.

Age is approximate; no birth dates, student status or employment status are
invented. Sensitivities use the lower/upper estimates, or only stable assignments:
lower >= 18 and upper < 25 for A; lower >= 35 for B. These definitions reproduce
the supplied sensitivity tables, including their boundary choices.

## 4. Fixed-day retention and standardisation

Only first entrants during 2015–2018 are cohort members. H is exactly 90 or 180
days. The primary event is a final exit on or before StartDate + H.

- An early known exit is an eligible failure.
- An observed interval reaching the horizon is eligible.
- An interval censored before the horizon is excluded.
- RetainedN / EligibleN is the raw cohort retention rate.

For each exact joining-month/year cohort, calculate rates separately for A and
B. On cohorts with eligible members in both groups, the common weight is:

```text
weight_cohort = (EligibleNA + EligibleNB) / sum(EligibleNA + EligibleNB)
MatchedRateA = sum(weight_cohort * RetentionRateA)
MatchedRateB = sum(weight_cohort * RetentionRateB)
GapPP_AminusB = 100 * (MatchedRateA - MatchedRateB)
```

The main sample has common support in all 48 month/year cohorts. Sensitivity
variants include lower/upper age bounds, stable assignments, treating the final
day as included, excluding pairs with either group below 20, and equal cohort
weights. The final-day-inclusive variant counts exits strictly before the
horizon as failures.

Summary scopes overlap: All 2015–2018, individual years, March/September/October
and other months. Select exactly one scope and one horizon; do not average
across these overlapping summaries. Recorded retention is not proof of paid
continuity or attendance.

## 5. Earlier descriptive views

ActivityByAge uses the original recorded-age groups 18–24 and 25+, with the
full source history. A source activity flag indicates ever being enrolled in
that category, not a visit count. Categories overlap.

ActivityVarietyByAgeGender averages NumberOfActivities within original recorded
age bands and gender. Under-18 records, including source age-zero values, remain
in this legacy descriptive view so it does not silently change the earlier
chart's population. This differs from the entry-age comparison's age exclusions.

Renewals is the distribution of the source seasonal renewal total. Zero
renewals does not mean zero subsequent visits. Usage averages source
AverageFrequency across customers over their whole observed membership and
source Ratio across customers over their final usage window. Ratio already
uses a 0–100 percentage scale; it is preserved, not multiplied by 100 again.

## 6. Source anomalies and unavailable history

Source values are retained. SourceChecks flags final-window dates that fall
outside enrolment dates, unusually long final windows and differences between
the stored Ratio and uncapped actual/allowed visits. These checks are reported
separately from critical identifier/date/status validation. No silent trimming,
reclassification or correction is used to force a match.

The database build is a new physical implementation of the supplied logical
model. It does not establish that the team previously loaded or queried this
SQLite database. No transaction-level payment/renewal history, tariff history,
causal uplift or revenue forecast can be recovered from these summaries.
