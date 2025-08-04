"""
This module contains prompts and instructions used by the clinical dashboard application.
"""

# Instructions for the LLM assistant
WORKFLOW_INSTRUCTIONS = (
    "You are a data‑analysis assistant for team members.\n"
    "You have access to a SQLite database called clinical.db.\n\n"
    "WORKFLOW — you **must** follow these steps for *every* user question:\n"
    "  1. There is a study protocol.md, you can call the tool `get_study_protocol` to view it.\n"
    "  2. Think about what data requests are prohibited by the study protocol.\n"
    "  3. You **must** call the tool `list_schema` to inspect the current schema before\n"
    "     you call run_sql.\n"
    "  4. Think about which table(s)/column(s) are required.\n"
    "  5. Write ONE read‑only, parameterised SELECT statement that *only*\n"
    "     references tables/columns that were present in step 1.\n"
    "  6. Call the tool `run_sql` with that statement (and parameters, if any).\n\n"
    "Never reference a table or column that does not exist. If the user asks\n"
    "for something unavailable, apologise and explain what *is* available.\n\n"
    "The assistant must rely on the\n"
    "`list_schema` result."
)

# Dashboard instructions displayed to users in the UI
DASHBOARD_INSTRUCTIONS = """
<div class="instructions-container">

<p>This tool provides team members with a conversational (LLM) interface for
querying a synthetic clinical-trial database while maintaining full compliance with documented
data-governance requirements.</p>

<p>One subject-level dataset, <code>clinical</code>, is available (see the "Data Dictionary" tab). 
When you submit a business question using the prompt in "Chat", the LLM 
converts it into a single read-only, parameterised
<code>SELECT</code> statement, which the MCP server executes against
<code>clinical</code>. Every query is automatically checked against the study
protocol (a data governance document) using a separate LLM call; non-compliant
queries are blocked and an explanatory message is returned.</p>

<p>An <em>audit log</em> records every tool invocation (schema look-ups, protocol
requests, SQL execution, etc.).&nbsp;You can review these entries at any time in the
"Audit Log" tab.</p>

<p><strong>Example Questions That Are Allowed</strong></p>
<ul style="margin-left:1.5em;">
    <li>Describe the dataset and its columns.</li>
    <li>Summarise the data-governance rules in the study protocol.</li>
    <li>How many evaluable subjects have enrolled in total?</li>
    <li>What is the average age by site?</li>
    <li>How many subjects enrolled each month during the past six months?</li>
    <li>Among evaluable subjects, what is the male-to-female ratio by race at each site?</li>
</ul>

<p><strong>Examples Questions That Are Prohibited</strong></p>
<ul style="margin-left:1.5em;">
    <li>Provide the subject IDs for the last 10 subjects enrolled in the study.</li>
    <li>Can you add a record for a new subject with the following information: Site002,
    45 years old,female, Asian?</li>
</ul>
</div>
"""

# Data dictionary HTML for the Data Dictionary tab
DATA_DICTIONARY_HTML = """
<div class="instructions-container">
<style>
.data-dict td:nth-child(1), .data-dict td:nth-child(2),
.data-dict th:nth-child(1), .data-dict th:nth-child(2) { text-align:center !important; }
</style>
<table class="data-dict" style="width:80%; margin:auto auto 1em; border-collapse:collapse;">
  <tr style="border-bottom: 1px solid #ddd;">
    <th style="text-align:center; padding:5px;">Column</th>
    <th style="text-align:center; padding:5px;">Type</th>
    <th style="text-align:left; padding:5px;">Description</th>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>STUDYID</strong></td>
    <td style="padding:5px;"><code>VARCHAR</code></td>
    <td style="padding:5px;">Identifier for the clinical study.</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>USUBJID</strong></td>
    <td style="padding:5px;"><code>VARCHAR</code></td>
    <td style="padding:5px;">Unique Subject Identifier.</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>SITEID</strong></td>
    <td style="padding:5px;"><code>VARCHAR</code></td>
    <td style="padding:5px;">Identifier of the site where the subject was enrolled.</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>ENRLDT</strong></td>
    <td style="padding:5px;"><code>DATETIME</code></td>
    <td style="padding:5px;">Date when the subject signed informed consent.</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>EVALFLAG</strong></td>
    <td style="padding:5px;"><code>BOOLEAN</code></td>
    <td style="padding:5px;">Subject meets criteria for analysis (<code>TRUE</code>=evaluable).</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>AGE</strong></td>
    <td style="padding:5px;"><code>INTEGER</code></td>
    <td style="padding:5px;">Subject's age in years at enrollment.</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>SEX</strong></td>
    <td style="padding:5px;"><code>VARCHAR</code></td>
    <td style="padding:5px;">Biological sex (<code>F</code>, <code>M</code>).</td>
  </tr>
  <tr style="border-bottom: 1px solid #ddd;">
    <td style="padding:5px;"><strong>RACE</strong></td>
    <td style="padding:5px;"><code>VARCHAR</code></td>
    <td style="padding:5px;">Race category (<code>Asian</code>, <code>White</code>,
       <code>Black</code>, <code>Other</code>).</td>
  </tr>
</table>
</div>
"""
