from __future__ import annotations
import os
import uuid
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from openai import OpenAI
from .db import get_engine


INTRO = (
    "To create your visualization I'll need a bit more information."
)


def generate_context_questions(history: list[dict]) -> list[str]:
    """Return up to 3 short context questions derived from chat history.

    The goal is to capture missing details required to build a useful chart.
    When no conversation history is supplied a default set of questions is
    returned.  The first question always includes a short statement requesting
    more info so the user understands why we are asking.
    """
    if not history:
        return [
            f"{INTRO} Which table or SQL query should I use as the data source?",
            "What fields should go on the x- and y-axes?",
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
        "Ask up to three short follow up questions covering: the data source or "
        "SQL query, which fields/metrics map to the axes, any filters or time "
        "ranges, and the desired chart type. "
        "Return the questions as a numbered list."
    )

    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=[{"role": "system", "content": prompt}] + messages,
        )
        text = completion.choices[0].message.content.strip()
        # Split lines and remove bullets/numbers
        lines = [line.lstrip("- ").lstrip("0123456789. ").strip() for line in text.splitlines() if line.strip()]
        if lines:
            lines[0] = f"{INTRO} {lines[0]}"
        return lines[:3]
    except Exception as e:
        print("generate_context_questions error", e)
        return [
            f"{INTRO} Which table or SQL query should I use as the data source?",
            "What fields should go on the x- and y-axes?",
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
    The file path to the image is returned.  An empty string is returned on
    failure.
    """

    if len(answers) < 4:
        return ""

    sql_query, x_col, y_col, chart_type = answers[:4]

    try:
        engine = get_engine()
        df = pd.read_sql_query(sql_query, engine)
    except Exception as e:  # noqa: BLE001
        print("create_matplotlib_visual query error", e)
        return ""

    if df.empty or x_col not in df.columns or y_col not in df.columns:
        print("create_matplotlib_visual no data or invalid columns")
        return ""

    fig, ax = plt.subplots()
    chart_type = chart_type.lower().strip()

    try:
        if chart_type == "line":
            ax.plot(df[x_col], df[y_col])
        elif chart_type == "scatter":
            ax.scatter(df[x_col], df[y_col])
        elif chart_type == "pie":
            ax.pie(df[y_col], labels=df[x_col], autopct="%1.1f%%")
        else:
            ax.bar(df[x_col], df[y_col])
    except Exception as e:  # noqa: BLE001
        print("create_matplotlib_visual plot error", e)
        return ""

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
        print("create_matplotlib_visual save error", e)
        return ""
    finally:
        plt.close(fig)

    return str(file_path)
