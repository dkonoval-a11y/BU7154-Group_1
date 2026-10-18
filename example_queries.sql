-- Inspect the customer-level view without duplicating customers through Activity.
SELECT COUNT(*) AS Customers,
       AVG(AverageFrequency) AS AverageVisitsPerWeek,
       AVG(Ratio) AS AverageFinalWindowUtilisationPct
FROM MemberSummary;

-- Number of members with each historical activity recorded.
SELECT Activity_Name, COUNT(*) AS Members
FROM Activity
GROUP BY Activity_Name
ORDER BY Members DESC;

-- Seasonal renewal counts. These are not visit counts or dated renewal events.
SELECT NumberOfRenewals, COUNT(*) AS Members
FROM MembershipStatus
GROUP BY NumberOfRenewals
ORDER BY NumberOfRenewals;

-- Original recorded-age categories, not estimated ages at joining.
SELECT CASE WHEN Age BETWEEN 18 AND 24 THEN '18-24' ELSE '25+' END AS RecordedAgeGroup,
       a.Activity_Name, COUNT(*) AS Members
FROM Member m
JOIN Activity a USING(Member_ID)
WHERE m.Age >= 18
GROUP BY RecordedAgeGroup, a.Activity_Name;

-- SQLite integrity and referential integrity checks.
PRAGMA integrity_check;
PRAGMA foreign_key_check;
