import os
import random
import uuid
from pathlib import Path

import requests
from moviepy import ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np


PROMPTS = [
    (
        "Generate an 8 second clip of a data professional summarizing the "
        "following table using complete sentences:\n{table}\nContext: {context}"
    ),
    (
        "Create a concise 8 second corporate style video explaining these "
        "metrics:\n{table}\nAdditional context: {context}"
    ),
    (
        "Produce an 8 second video of an analyst presenting this data in a "
        "professional setting:\n{table}\n{context}"
    ),
]

VEO_API_KEY = os.getenv("VEO_API_KEY")


def _latest_table(history: list[dict]) -> str | None:
    """Return the most recent table image path from chat history."""
    for msg in reversed(history):
        if msg.get("image") and "table" in msg.get("text", "").lower():
            return msg["image"]
    return None


def generate_directors_cut(history: list[dict]) -> str:
    """Create a short video for the latest table using Google Veo 3 when available."""
    img = _latest_table(history)
    if not img or not os.path.exists(img):
        raise ValueError("No table image found")

    txt_path = Path(img).with_suffix(".txt")
    table_text = txt_path.read_text() if txt_path.exists() else ""

    context = " ".join(m.get("text", "") for m in history if m.get("sender") == "user")
    context = context[-500:]
    prompt = random.choice(PROMPTS).format(table=table_text, context=context)

    output_dir = Path("charts")
    output_dir.mkdir(exist_ok=True)
    outfile = output_dir / f"directorscut_{uuid.uuid4().hex}.mp4"

    if VEO_API_KEY:
        try:
            resp = requests.post(
                "https://api.veo.com/v3/generate",
                headers={"Authorization": f"Bearer {VEO_API_KEY}"},
                json={"prompt": prompt},
                timeout=60,
            )
            resp.raise_for_status()
            video_url = resp.json().get("video_url")
            if video_url:
                r = requests.get(video_url, timeout=60)
                with open(outfile, "wb") as f:
                    f.write(r.content)
                return str(outfile)
        except Exception as e:  # noqa: BLE001
            print("Veo 3 API error", e)

    # Local fallback if API not available or failed
    try:
        clip = ImageClip(img).set_duration(8)
        text_img = Image.new("RGB", (clip.w, 80), "black")
        draw = ImageDraw.Draw(text_img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 10), prompt, fill="white", font=font)
        txt_clip = ImageClip(np.array(text_img)).set_duration(8).set_pos(("center", "bottom"))
        video = CompositeVideoClip([clip, txt_clip])
        video.write_videofile(str(outfile), fps=1, codec="libx264", audio=False, logger=None)
    except Exception:  # noqa: BLE001
        outfile.touch()

    return str(outfile)

