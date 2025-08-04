import asyncio
import datetime
import functools
import json
import sqlite3

import aiosqlite
import openai
from fastmcp.server import FastMCP

# Paths to files
DB_PATH = "clinical.db"
PROTOCOL_FILE = "support/study_protocol.md"

# ---------------------------------------------------------------------------
# 0️⃣  Audit log setup
# ---------------------------------------------------------------------------


async def setup_audit_log():
    """Create (or recreate) the audit_log table.
    The table is cleared on every server start so each session has a fresh log.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            arguments TEXT NOT NULL,
            approved BOOLEAN NOT NULL
        )
        """)
        # Clear previous logs so each run starts fresh
        await db.execute("DELETE FROM audit_log;")
        await db.commit()


def audit_log(func):
    """Decorator to log tool usage."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get tool name from the function
        tool_name = func.__name__

        arguments = json.dumps({"args": args, "kwargs": kwargs}, default=str)

        # All tools except run_sql are approved
        approved = tool_name != "run_sql"

        # Call the original function
        result = await func(*args, **kwargs)

        # For run_sql, check if it was approved based on result
        if tool_name == "run_sql" and isinstance(result, dict) and "error" not in result:
            approved = True

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                (
                    "INSERT INTO audit_log (timestamp, tool_name, arguments, approved) "
                    "VALUES (?, ?, ?, ?)"
                ),
                (
                    datetime.datetime.now(),
                    tool_name,
                    arguments,
                    approved,
                ),
            )
            await db.commit()

        return result

    return wrapper


# ---------------------------------------------------------------------------
# Helper: LLM policy gate
# ---------------------------------------------------------------------------


async def llm_policy_check(sql: str) -> tuple[bool, str]:
    """Ask GPT-4o whether the SQL violates the study protocol.

    Returns:
        (allowed, reason)
    """

    with open(PROTOCOL_FILE, "r", encoding="utf-8") as f:
        protocol_text = f.read()

    # Build prompt – keep it short and deterministic
    messages = [
        {
            "role": "system",
            "content": (
                "You are a data-governance gatekeeper. "
                "Given a study protocol and a SQL query, respond with JSON: "
                '{"allowed": true/false, "reason": "..."}. '
                "If any rule is violated, set allowed to false and provide the specific reason "
                "based on the protocol. "
                "Unless a rule is explicitly and clearly violated, set allowed to true."
            ),
        },
        {"role": "system", "content": protocol_text},
        {
            "role": "user",
            "content": f"SQL query to evaluate:\n{sql}\nDoes it violate the study protocol?",
        },
    ]

    try:
        client = openai.OpenAI()
        resp = client.chat.completions.create(model="gpt-4o", temperature=0, messages=messages)
        reply = resp.choices[0].message.content.strip()

        # Strip markdown code blocks if present
        if reply.startswith("```json") and reply.endswith("```"):
            reply = reply[7:-3].strip()
        elif reply.startswith("```") and reply.endswith("```"):
            reply = reply[3:-3].strip()

        try:
            data = json.loads(reply)
            allowed = bool(data.get("allowed"))
            reason = data.get("reason")
        except json.JSONDecodeError as e:
            # If we can't parse the JSON, treat it as a failure in the LLM check
            raise Exception(f"Failed to parse LLM response as JSON: {e}. Response was: {reply}")

        if not reason or reason == "No reason returned.":
            if allowed:
                reason = "Query complies with all study protocol requirements."
            else:
                reason = (
                    "Query potentially violates study protocol. Please review and ensure "
                    "it doesn't expose subject identifiers."
                )
    except Exception as exc:
        # Fail-safe: deny if LLM check fails
        allowed = False
        reason = f"LLM policy check failed: {exc}"

    return allowed, reason


# ---------------------------------------------------------------------------
# 1️⃣  Build the server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="Clinical SQL MCP",
)

# ---------------------------------------------------------------------------
# 2️⃣  Tool: list_schema
# ---------------------------------------------------------------------------


@mcp.tool(name="list_schema")
@audit_log
async def list_schema() -> dict:
    """Return a dictionary of table schemas including *column names* and *data types*.

    This tool should be called **first** so the assistant can understand which
    tables and columns exist _and_ what data type each column holds.

    Returns format:
        {
            "table_name": {
                "COLUMN_A": "TEXT",
                "COLUMN_B": "INTEGER",
                ...
            },
            ...
        }
    """
    async with aiosqlite.connect(DB_PATH) as db:
        tbl_cur = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in await tbl_cur.fetchall() if row[0].lower() != "audit_log"]

        schema: dict[str, dict[str, str]] = {}
        for t in tables:
            col_cur = await db.execute(f"PRAGMA table_info({t});")
            # SQLite PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
            schema[t] = {row[1]: row[2] for row in await col_cur.fetchall()}
        return schema


# ---------------------------------------------------------------------------
# 3️⃣  Tool: get_study_protocol
# ---------------------------------------------------------------------------


@mcp.tool(name="get_study_protocol")
@audit_log
async def get_study_protocol() -> str:
    """Return the study protocol markdown document.

    The server provides this document to explain the data governance rules
    defined in *study_protocol.md*.
    """
    # Read protocol file contents
    with open(PROTOCOL_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return content


# ---------------------------------------------------------------------------
# 3️⃣  Tool: run_sql
# ---------------------------------------------------------------------------


@mcp.tool(name="run_sql")
@audit_log
async def run_sql(query: str, params: list | None = None) -> dict:
    """Execute a SQL query against the clinical database and return the results.

    Parameters:
        query: A SQL SELECT statement (only SELECT statements are allowed)
        params: Optional list of parameters for parameterized queries

    Returns:
        A dictionary with "rows" (list of row dictionaries) and "rowcount" (number of rows)
        Or a dictionary with "error" (error message) if the query violates the protocol

    Always call list_schema first to verify table and column names.

    Note:
        All governance and privacy restrictions are documented in
        study_protocol.md. The client MUST consult and adhere to that
        protocol before issuing queries.
    """
    # Ask LLM if the query is allowed under the study protocol
    allowed, reason = await llm_policy_check(query)
    if not allowed:
        # Return a message instead of raising an error
        return {
            "error": (
                f"Protocol violation: {reason}. You can view the study protocol "
                f"with the get_study_protocol tool."
            ),
            "rows": [],
            "rowcount": 0,
        }

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        try:
            async with db.execute(query, params or []) as cur:
                rows = [dict(r) async for r in cur]
        except sqlite3.OperationalError as e:
            # Surface a clear message so the assistant can correct itself
            return {
                "error": f"SQL error: {e}. Did you check list_schema first?",
                "rows": [],
                "rowcount": 0,
            }

    result = {"rows": rows, "rowcount": len(rows)}

    return result


# ---------------------------------------------------------------------------
# 5️⃣  Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(setup_audit_log())
    # Always use port 8000 for MCP server
    port = 8000
    # Always bind to all interfaces in container environment
    host = "0.0.0.0"
    print(f"Starting MCP server on {host}:{port}")
    mcp.run(transport="sse", host=host, port=port)
