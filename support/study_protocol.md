# Study Protocol: Data Governance and Access Control

## 1. Overview
This protocol outlines the governance policies for accessing and analyzing data within the Clinical SQL MCP environment. All users (including automated agents) **must acknowledge and adhere to these rules before every data query**.

## 2. Data Dictionary
| Column   | Type     | Description                                                         |
|----------|----------|---------------------------------------------------------------------|
| **STUDYID** | `VARCHAR` | Identifier for the clinical study. |
| **USUBJID** | `VARCHAR` | Unique Subject Identifier. |
| **SITEID**  | `VARCHAR` | Identifier of the investigator site where the subject was enrolled. |
| **ENRLDT**  | `DATETIME` | Original date when the subject signed informed consent / was enrolled. |
| **EVALFLAG** | `BOOLEAN` | Indicates whether the subject meets the study’s criteria for inclusion in the primary analysis set (`TRUE` = evaluable). |
| **AGE**     | `INTEGER` | Subject’s age **in years** at the time of enrollment (`ENRLDT`). |
| **SEX**     | `VARCHAR` | Biological sex as recorded at enrollment (`F`, `M`). |
| **RACE**    | `VARCHAR` | Race or ethnicity category per the protocol’s CRF (`Asian`, `White`, `Black`, `Other`). |

## 3. Approved Data Operations
- Read-only analytic queries: SQL `SELECT` statements only.
- Aggregations (e.g. `COUNT`, `AVG`, `SUM`, `MIN`, `MAX`, `GROUP BY`).
- Parameterised queries using positional (`?`) placeholders.

## 4. Privacy Protection
- USUBJID must **never** be selected or returned, but can otherwise be used in any query or aggregation. 
- Any query that returns *raw, subject-level rows* must yield at least **5** unique subjects.
- Aggregation queries (see §3) are exempt from the above rule.

## 5. Prohibited Queries
- Non-SELECT statements (`INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, etc.).
- Attempts to join or combine datasets for re-identification purposes.

## 6. Example Queries
| Query | Allowed? | Reason |
|-------|----------|--------|
| `SELECT COUNT(*) FROM clinical WHERE SITEID = "Site001";` | ✅ | Aggregated count only. |
| `SELECT USUBJID, AGE FROM clinical WHERE SITEID = "Site001";` | ❌ | Returning USUBJID is prohibited. |
| `UPDATE clinical SET AGE = AGE + 1;` | ❌ | Non-SELECT statement. |

## 7. Revision History
| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2025-07-31 | Initial protocol derived from embedded restrictions in `clinical_mcp.py`. | 