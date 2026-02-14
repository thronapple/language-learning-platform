import os
import textwrap
from typing import List

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - Pillow may not be available in some envs
    Image = None  # type: ignore


class ExportService:
    def __init__(self, repo=None, storage=None) -> None:
        self.repo = repo
        self.storage = storage

    def _get_content_text(self, content_id: str) -> str:
        if not self.repo:
            return "Export preview"
        doc = self.repo.get("content", content_id)
        if not doc:
            return "Export preview"
        segs: List[str] = doc.get("segments") or []
        if segs:
            return "\n".join(segs)
        return doc.get("text") or "Export preview"

    def longshot(self, content_id: str) -> str:
        text = self._get_content_text(content_id)
        os.makedirs("exports", exist_ok=True)
        outfile = os.path.join("exports", f"longshot_{content_id}.png")

        if Image is None:
            # Fallback: create an empty marker file
            with open(outfile, "wb") as f:
                f.write(b"")
            return outfile

        width = 1080
        margin = 60
        font_size = 40
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # Wrap text roughly to fit width
        wrapper = textwrap.TextWrapper(width=35)
        lines = []
        for para in text.split("\n"):
            lines.extend(wrapper.wrap(para) or [""])

        line_height = font_size + 16
        height = margin * 2 + line_height * max(1, len(lines))
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = margin
        for line in lines:
            draw.text((margin, y), line, fill=(20, 20, 20), font=font)
            y += line_height

        img.save(outfile, format="PNG")
        if self.storage:
            remote_path = f"exports/{os.path.basename(outfile)}"
            return self.storage.upload_file(outfile, remote_path)
        return outfile
