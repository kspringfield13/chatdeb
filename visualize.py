from __future__ import annotations
import os
import uuid
import json
import textwrap
import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from .db import get_engine
from .chart_style import set_default_style
from .config import CHARTS_DIR

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
            "Query must be a SELECT statement. For example: " "SELECT * FROM your_table"
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

    charts_dir = CHARTS_DIR
    file_path = charts_dir / f"chart_{uuid.uuid4().hex}.png"
    try:
        fig.savefig(file_path, dpi=300, facecolor="#1f1f1f")
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"Saving chart failed: {e}") from e
    finally:
        plt.close(fig)

    return str(file_path)


def _prettify_headers(headers: list[str]) -> list[str]:
    """Return nicer header labels."""
    return [h.replace("_", " ").title() for h in headers]


def create_table_visual(
    rows: list[tuple],
    limit: int | None = None,
    headers: list[str] | None = None,
    cell_char_limit: int = 20,
    header_char_limit: int = 12,
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

    df = pd.DataFrame(display_rows)

    if headers and len(headers) == df.shape[1]:
        pretty_headers = _prettify_headers(headers)
    else:
        pretty_headers = infer_headers(display_rows)
    df.columns = pretty_headers
    wrapped_headers = [textwrap.fill(h, width=header_char_limit) for h in pretty_headers]
    header_line_counts = [h.count("\n") + 1 for h in wrapped_headers]
    max_header_lines = max(header_line_counts)

    is_numeric = [pd.api.types.is_numeric_dtype(df[col]) for col in df.columns]

    for col, numeric in zip(df.columns, is_numeric):
        if numeric:
            df[col] = df[col].apply(
                lambda x: f"{x:,.0f}" if isinstance(x, int) or (isinstance(x, float) and x.is_integer()) else f"{x:,.2f}"
            )

    def _truncate(x: object) -> str:
        s = str(x)
        return s if len(s) <= cell_char_limit else s[: cell_char_limit - 1] + "\u2026"

    df = df.astype(str).map(_truncate)

    charts_dir = CHARTS_DIR
    file_path = charts_dir / f"table_{uuid.uuid4().hex}.png"
    text_path = file_path.with_suffix(".txt")

    try:
        n_rows, n_cols = df.shape
        fig_width = min(max(n_cols * 0.8, 4), 10)
        extra_height = (max_header_lines - 1) * 0.5
        fig_height = min(max(n_rows * 0.5 + 1 + extra_height, 2), 8)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        fig.patch.set_facecolor("#1f1f1f")
        ax.axis("off")
        ax.set_frame_on(True)
        ax.patch.set_facecolor("#1f1f1f")

        col_width = 0.9 / n_cols if n_cols else 0.9
        table = ax.table(
            cellText=df.values,
            colLabels=wrapped_headers,
            cellLoc="center",
            loc="center",
            colWidths=[col_width] * n_cols,
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1)

        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#777777")
            cell.set_linewidth(0.5)
            if row == 0:
                cell.set_facecolor("#333333")
                cell.set_text_props(weight="bold", color="white")
                cell.set_height(cell.get_height() * header_line_counts[col])
            else:
                cell.set_facecolor("#1f1f1f")
                cell.set_text_props(color="#e0e0e0")
                if is_numeric[col]:
                    cell.get_text().set_ha("right")
                else:
                    cell.get_text().set_ha("left")

        fig.tight_layout()
        fig.savefig(file_path, bbox_inches="tight", dpi=300, facecolor="#1f1f1f")
        try:
            df.to_csv(text_path, index=False)
        except Exception as e:
            print("create_table_visual text error", e)
    except Exception as e:  # noqa: BLE001
        print("create_table_visual save error", e)
        return ""
    finally:
        plt.close(fig)

    return str(file_path)


def _refine_answers_with_llm(
    answers: list[str], history: list[dict] | None = None
) -> list[str]:
    """Return improved visualization answers using OpenAI if available."""

    try:
        client = OpenAI()
    except Exception as e:  # noqa: BLE001
        print("refine answers openai error", e)
        return answers

    system = (
        "You are a data assistant. Given the conversation and the user's initial "
        "answers, produce a valid SQL SELECT query, an x column, a y column and "
        "a chart type. If information is missing or invalid, make reasonable "
        'assumptions. Respond with JSON in the form {"sql":..., "x":..., '
        '"y":..., "type":...}.'
    )

    messages = [{"role": "system", "content": system}]
    if history:
        for entry in history[-5:]:
            role = "user" if entry.get("sender") == "user" else "assistant"
            txt = entry.get("text", "")
            messages.append({"role": role, "content": txt})

    messages.append({"role": "user", "content": str(answers)})

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0,
        )
        text = completion.choices[0].message.content.strip()
        data = json.loads(text)
        return [
            data.get("sql", answers[0]),
            data.get("x", answers[1]),
            data.get("y", answers[2]),
            data.get("type", answers[3]),
        ]
    except Exception as e:  # noqa: BLE001
        print("refine answers parse error", e)
        return answers


def create_visual_with_fallback(
    answers: list[str], history: list[dict] | None = None
) -> str:
    """Attempt to create a chart, retrying with LLM-refined answers."""

    try:
        return create_matplotlib_visual(answers)
    except ValueError as e:
        new_answers = _refine_answers_with_llm(answers, history)
        if new_answers != answers:
            try:
                return create_matplotlib_visual(new_answers)
            except Exception as e2:  # noqa: BLE001
                print("fallback visualization error", e2)
        raise e
