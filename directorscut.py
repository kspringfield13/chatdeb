import os
import random
import uuid
import json
import base64
from pathlib import Path

import requests
from moviepy import (
    ImageClip,
    CompositeVideoClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image, ImageDraw, ImageFont
from .config import CHARTS_DIR
import numpy as np
from openai import OpenAI


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

# Small 1-second blank MP4 used if video rendering fails
_PLACEHOLDER_B64 = (
    "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAs1tZGF0AAACrQYF//+p3EXp"
    "vebZSLeWLNgg2SPu73gyNjQgLSBjb3JlIDE2NCByMzE5MSA0NjEzYWMzIC0gSC4yNjQvTVBFRy00IEFW"
    "QyBjb2RlYyAtIENvcHlsZWZ0IDIwMDMtMjAyNCAtIGh0dHA6Ly93d3cudmlkZW9sYW4ub3JnL3gyNjQu"
    "aHRtbCAtIG9wdGlvbnM6IGNhYmFjPTEgcmVmPTMgZGVibG9jaz0xOjA6MCBhbmFseXNlPTB4MzoweDEx"
    "MyBtZT1oZXggc3VibWU9NyBwc3k9MSBwc3lfcmQ9MS4wMDowLjAwIG1peGVkX3JlZj0xIG1lX3Jhbmdl"
    "PTE2IGNocm9tYV9tZT0xIHRyZWxsaXM9MSA4eDhkY3Q9MSBjcW09MCBkZWFkem9uZT0yMSwxMSBmYXN0"
    "X3Bza2lwPTEgY2hyb21hX3FwX29mZnNldD0tMiB0aHJlYWRzPTEgbG9va2FoZWFkX3RocmVhZHM9MSBz"
    "bGljZWRfdGhyZWFkcz0wIG5yPTAgZGVjaW1hdGU9MSBpbnRlcmxhY2VkPTAgYmx1cmF5X2NvbXBhdD0w"
    "IGNvbnN0cmFpbmVkX2ludHJhPTAgYmZyYW1lcz0zIGJfcHlyYW1pZD0yIGJfYWRhcHQ9MSBiX2JpYXM9"
    "MCBkaXJlY3Q9MSB3ZWlnaHRiPTEgb3Blbl9nb3A9MCB3ZWlnaHRwPTIga2V5aW50PTI1MCBrZXlpbnRf"
    "bWluPTEgc2NlbmVjdXQ9NDAgaW50cmFfcmVmcmVzaD0wIHJjX2xvb2thaGVhZD00MCByYz1jcmYgbWJ0"
    "cmVlPTEgY3JmPTIzLjAgcWNvbXA9MC42MCBxcG1pbj0wIHFwbWF4PTY5IHFwc3RlcD00IGlwX3JhdGlv"
    "PTEuNDAgYXE9MToxLjAwAIAAAAAQZYiEABX//vfJ78Cm69vfgQAAAwNtb292AAAAbG12aGQAAAAAAAAA"
    "AAAAAAAAAAPoAAAD6AABAAABAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAA"
    "AEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAACLnRyYWsAAABcdGtoZAAAAAMAAAAAAAAA"
    "AAAAAAEAAAAAAAAD6AAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAA"
    "AEAAAAAAEAAAABAAAAAAACRlZHRzAAAAHGVsc3QAAAAAAAAAAQAAA+gAAAAAAAEAAAAAAaZtZGlhAAAA"
    "IG1kaGQAAAAAAAAAAAAAAAAAAEAAAABAAFXEAAAAAAAtaGRscgAAAAAAAAAAdmlkZQAAAAAAAAAAAAAA"
    "AFZpZGVvSGFuZGxlcgAAAAFRbWluZgAAABR2bWhkAAAAAQAAAAAAAAAAAAAAJGRpbmYAAAAcZHJlZgAA"
    "AAAAAAABAAAADHVybCAAAAABAAABEXN0YmwAAACtc3RzZAAAAAAAAAABAAAAnWF2YzEAAAAAAAAAAQAA"
    "AAAAAAAAAAAAAAAAAAAAEAAQAEgAAABIAAAAAAAAAAEUTGF2YzYxLjMuMTAwIGxpYngyNjQAAAAAAAAA"
    "AAAAAAAY//8AAAAzYXZjQwFkAAr/4QAWZ2QACqzZXoQAAAMABAAAAwAIPEiWWAEABmjr48siwP34+AAA"
    "AAAUYnRydAAAAAAAABYoAAAWKAAAABhzdHRzAAAAAAAAAAEAAAABAABAAAAAABxzdHNjAAAAAAAAAAEA"
    "AAABAAAAAQAAAAEAAAAUc3RzegAAAAAAAALFAAAAAQAAABRzdGNvAAAAAAAAAAEAAAAwAAAAYXVkdGEA"
    "AABZbWV0YQAAAAAAAAAhaGRscgAAAAAAAAAAbWRpcmFwcGwAAAAAAAAAAAAAAAAsaWxzdAAAACSpdG9v"
    "AAAAHGRhdGEAAAABAAAAAExhdmY2MS4xLjEwMA=="
)


def _latest_table(history: list[dict]) -> str | None:
    """Return the most recent table image path from chat history."""
    for msg in reversed(history):
        if msg.get("image") and "table" in msg.get("text", "").lower():
            return msg["image"]
    return None


def _generate_veo_prompts(table_text: str, context: str) -> tuple[str, str]:
    """Return two short video prompts via OpenAI or fall back to defaults."""
    try:
        client = OpenAI()
        system = (
            "You craft concise prompts for a video generation model. "
            "Using the provided table and context, write two separate prompts "
            "(each under 50 words) that introduce and conclude a short data "
            'story video. Respond with JSON like {"first":..., "second":...}.'
        )
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"TABLE:\n{table_text}\nCONTEXT:\n{context}",
                },
            ],
            temperature=0.7,
        )
        data = json.loads(resp.choices[0].message.content)
        first, second = data.get("first"), data.get("second")
        if isinstance(first, str) and isinstance(second, str):
            return first, second
    except Exception as e:  # noqa: BLE001
        print("generate_veo_prompts error", e)

    p1 = random.choice(PROMPTS).format(table=table_text, context=context)
    p2 = random.choice(PROMPTS).format(table=table_text, context=context)
    return p1, p2


def generate_directors_cut(history: list[dict]) -> str:
    """Create a short video for the latest table using Google Veo 3 when available."""
    img = _latest_table(history)
    if not img or not os.path.exists(img):
        raise ValueError("No table image found")

    txt_path = Path(img).with_suffix(".txt")
    table_text = txt_path.read_text() if txt_path.exists() else ""

    context = " ".join(m.get("text", "") for m in history if m.get("sender") == "user")
    context = context[-500:]
    p1, p2 = _generate_veo_prompts(table_text, context)

    output_dir = CHARTS_DIR
    outfile = output_dir / f"directorscut_{uuid.uuid4().hex}.mp4"

    if VEO_API_KEY:
        try:
            clips: list[VideoFileClip] = []
            for prm in (p1, p2):
                resp = requests.post(
                    "https://api.veo.com/v3/generate",
                    headers={"Authorization": f"Bearer {VEO_API_KEY}"},
                    json={"prompt": prm},
                    timeout=60,
                )
                resp.raise_for_status()
                url = resp.json().get("video_url")
                if not url:
                    raise ValueError("missing video_url")
                r = requests.get(url, timeout=60)
                tmp_path = output_dir / f"tmp_{uuid.uuid4().hex}.mp4"
                with open(tmp_path, "wb") as f:
                    f.write(r.content)
                clips.append(VideoFileClip(str(tmp_path)))
            video = concatenate_videoclips(clips)
            if video.duration > 15:
                video = video.subclip(0, 15)
            video.write_videofile(
                str(outfile), codec="libx264", audio=False, logger=None
            )
            for c in clips:
                c.close()
            for tmp in output_dir.glob("tmp_*.mp4"):
                tmp.unlink(missing_ok=True)
            return str(outfile)
        except Exception as e:  # noqa: BLE001
            print("Veo 3 API error", e)

    # Local fallback if API not available or failed
    try:
        clip1 = ImageClip(img).set_duration(7.5)
        text_img = Image.new("RGB", (clip1.w, 80), "black")
        draw = ImageDraw.Draw(text_img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        draw.text((10, 10), p1, fill="white", font=font)
        txt_clip1 = (
            ImageClip(np.array(text_img))
            .set_duration(7.5)
            .set_pos(("center", "bottom"))
        )
        video1 = CompositeVideoClip([clip1, txt_clip1])

        clip2 = ImageClip(img).set_duration(7.5)
        text_img2 = Image.new("RGB", (clip2.w, 80), "black")
        draw2 = ImageDraw.Draw(text_img2)
        draw2.text((10, 10), p2, fill="white", font=font)
        txt_clip2 = (
            ImageClip(np.array(text_img2))
            .set_duration(7.5)
            .set_pos(("center", "bottom"))
        )
        video2 = CompositeVideoClip([clip2, txt_clip2])

        video = concatenate_videoclips([video1, video2])
        if video.duration > 15:
            video = video.subclip(0, 15)
        video.write_videofile(
            str(outfile), fps=1, codec="libx264", audio=False, logger=None
        )
    except Exception:  # noqa: BLE001
        try:
            outfile.write_bytes(base64.b64decode(_PLACEHOLDER_B64))
        except Exception:
            outfile.touch()

    return str(outfile)
