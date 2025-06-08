from __future__ import annotations
import os
import uuid
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from .db import get_engine
from .chart_style import set_default_style

set_default_style()


def infer_headers(rows: list[tuple]) -> list[str]:
    """Generate fallback column headers based on sample data types."""
    if not rows:
        return []

    num_cols = len(rows[0])
    headers: list[str] = []

    for idx in range(num_cols):
        sample = None
        for row in rows:
            if idx < len(row) and row[idx] is not None:
                sample = row[idx]
                break

        label = "Value"
        if isinstance(sample, (int, float)):
            label = "Number"
        elif isinstance(sample, str):
            try:
                pd.to_datetime(sample)
                label = "Date"
            except Exception:
                if sample.isdigit() or "_" in sample or "-" in sample:
                    label = "ID"
                else:
                    label = "Text"

        headers.append(f"{label} {idx + 1}")

    return headers


INTRO = "To create a visualization for you, I need some more details:"


def generate_context_questions(history: list[dict]) -> list[str]:
    """Return up to 4 short context questions derived from chat history.

    The goal is to capture missing details required to build a useful chart.
    When no conversation history is supplied a default set of questions is
    returned.  The first question always includes a short statement requesting
    more info so the user understands why we are asking.
    """
    if not history:
        return [
            f"{INTRO} Which table or SQL query should I use as the data source?",
            "Which column should be used for the x-axis?",
            "Which column or metric goes on the y-axis?",
            "What chart type would you like (bar, line, scatter, etc.)?",
        ]

    messages = []
    for entry in history:
        role = "user" if entry.get("sender") == "user" else "assistant"
        text = entry.get("text", "")
        messages.append({"role": role, "content": text})

    prompt = (
        "You are preparing to create a visualization for the user. "
        "Review the conversation and determine what additional details are needed "
        "to construct an accurate chart. "
        "Ask exactly four short follow up questions in this order: the data source "
        "or SQL query, the x-axis field, the y-axis field, and the desired chart "
        "type. Return the questions as a numbered list."
    )

    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": prompt}] + messages,
        )
        text = completion.choices[0].message.content.strip()
        # Split lines and remove bullets/numbers
        lines = [
            line.lstrip("- ").lstrip("0123456789. ").strip()
            for line in text.splitlines()
            if line.strip()
        ]
        if len(lines) == 4 and all(q.endswith("?") for q in lines):
            lines[0] = f"{INTRO} {lines[0]}"
            return lines
    except Exception as e:  # noqa: BLE001
        print("generate_context_questions error", e)

    return [
        f"{INTRO} Which table or SQL query should I use as the data source?",
        "Which column should be used for the x-axis?",
        "Which column or metric goes on the y-axis?",
        "What chart type would you like (bar, line, scatter, etc.)?",
    ]


def create_matplotlib_visual(answers: list[str]) -> str:
    """Create a chart locally using matplotlib and return the image path.

    ``answers`` is expected to contain at least four elements in the
    following order:

    1. An SQL query that returns the data for the chart.
    2. The column to use for the x-axis.
    3. The column or metric for the y-axis.
    4. The desired chart type (``bar``, ``line``, ``scatter`` or ``pie``).

    The function will execute the query against the DuckDB database,
    generate the chart and save it under the ``charts`` directory.
    The file path to the image is returned.  ``ValueError`` is raised if the
    query fails or the provided parameters are invalid.
    """

    if len(answers) < 4:
        raise ValueError(
            "Four answers are required: SQL, x column, y column and chart type"
        )

    sql_query, x_col, y_col, chart_type = answers[:4]
    if not sql_query.strip().lower().startswith("select"):
        raise ValueError(
            "Query must be a SELECT statement. For example: "
            "SELECT * FROM your_table"
        )

    try:
        engine = get_engine()
        df = pd.read_sql_query(sql_query, engine)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Query failed: {e}") from e

    if df.empty:
        raise ValueError("Query returned no data")
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError("Invalid column names for x or y axis")

    fig, ax = plt.subplots()
    chart_type = chart_type.lower().strip()

    try:
        if chart_type == "line":
            ax.plot(df[x_col], df[y_col])
        elif chart_type == "scatter":
            ax.scatter(df[x_col], df[y_col])
        elif chart_type == "pie":
            ax.pie(df[y_col], labels=df[x_col], autopct="%1.1f%%")
        elif chart_type == "bar":
            ax.bar(df[x_col], df[y_col])
        else:
            raise ValueError(f"Unsupported chart type '{chart_type}'")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Plotting failed: {e}") from e

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} vs {x_col}")
    fig.tight_layout()

    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    file_path = charts_dir / f"chart_{uuid.uuid4().hex}.png"
    try:
        fig.savefig(file_path)
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Saving chart failed: {e}") from e
    finally:
        plt.close(fig)

    return str(file_path)


def create_table_visual(
    rows: list[tuple],
    limit: int | None = None,
    headers: list[str] | None = None,
    cell_char_limit: int = 20,
) -> str:
    """Create a table image from ``rows`` and return the path.

    ``rows`` is a list of tuples representing table rows. Optional
    ``headers`` may be provided to label the columns. When ``headers`` is
    omitted or does not match the number of columns, generic labels are used.
    The resulting PNG has a transparent background and subtle styling so it
    can be displayed over any UI theme.
    """

    if not rows:
        return ""

    display_rows = rows[:limit] if limit is not None else rows

    def _truncate(x: object) -> str:
        s = str(x)
        return s if len(s) <= cell_char_limit else s[: cell_char_limit - 1] + "\u2026"

    # ``applymap`` is deprecated so use ``DataFrame.map`` for element-wise
    # transformation across the entire DataFrame. This avoids the FutureWarning
    # seen in tests and is slightly faster.
    df = pd.DataFrame(display_rows).map(_truncate)

    if headers and len(headers) == df.shape[1]:
        df.columns = headers
    else:
        df.columns = infer_headers(display_rows)

    charts_dir = Path("charts")
    charts_dir.mkdir(exist_ok=True)
    file_path = charts_dir / f"table_{uuid.uuid4().hex}.png"

    try:
        fig, ax = plt.subplots()
        fig.patch.set_facecolor("#1f1f1f")
        ax.axis("off")
        ax.set_frame_on(False)
        ax.patch.set_facecolor("#1f1f1f")

        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc="center",
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(14)
        table.scale(1, 1.4)
        table.auto_set_column_width(col=list(range(len(df.columns))))

        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#777777")
            cell.set_linewidth(0.5)
            if row == 0:
                cell.set_facecolor("#333333")
                cell.set_text_props(weight="bold", color="white")
            else:
                cell.set_facecolor("#1f1f1f")
                cell.set_text_props(color="#e0e0e0")

        fig.tight_layout()
        fig.savefig(file_path, bbox_inches="tight")
    except Exception as e:  # noqa: BLE001
        print("create_table_visual save error", e)
        return ""
    finally:
        plt.close(fig)

    return str(file_path)
