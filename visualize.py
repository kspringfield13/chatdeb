from __future__ import annotations
import os
from openai import OpenAI
import requests


def generate_context_questions(history: list[dict]) -> list[str]:
    """Return up to 3 short context questions derived from chat history."""
    if not history:
        return []

    messages = []
    for entry in history:
        role = "user" if entry.get("sender") == "user" else "assistant"
        text = entry.get("text", "")
        messages.append({"role": role, "content": text})

    prompt = (
        "You are preparing to create a visualization for the user. "
        "Based on the conversation so far, propose up to 3 concise questions that "
        "will confirm the metrics and values the user wants to see. "
        "Return them as a numbered list."
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
        return lines[:3]
    except Exception as e:
        print("generate_context_questions error", e)
        return []


def create_superset_visual(answers: list[str]) -> str:
    """Attempt to create a Superset chart and return its URL.

    This is a placeholder implementation that demonstrates how one could
    call Superset's REST API. It expects SUPERSET_BASE_URL and
    SUPERSET_API_KEY in the environment. If those variables are missing or
    any request fails, the base URL is returned so the frontend can load
    Superset manually.
    """
    base_url = os.getenv("SUPERSET_BASE_URL", "")
    api_key = os.getenv("SUPERSET_API_KEY")
    if not base_url:
        return ""

    if not api_key:
        return base_url

    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "slice_name": "KYDxBot Chart",
            "viz_type": "table",
            "params": {"metrics": answers},
        }
        resp = requests.post(f"{base_url.rstrip('/')}/api/v1/chart/", json=payload, headers=headers)
        resp.raise_for_status()
        chart_id = resp.json().get("id")
        if chart_id:
            return f"{base_url.rstrip('/')}/explore/?slice_id={chart_id}"
    except Exception as e:
        print("create_superset_visual error", e)

    return base_url
