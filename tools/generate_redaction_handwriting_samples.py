from __future__ import annotations

"""Generate deterministic, synthetic handwritten-style redaction test images."""

from pathlib import Path
from random import Random

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "test_artifacts" / "redaction_handwriting_20260719" / "samples"
FONT_PATH = Path(r"C:\Windows\Fonts\simkai.ttf")

SAMPLES = {
    "handwriting_sensitive_clear.png": [
        "1. 请说明社会存在与社会意识的关系。",
        "姓名：测试甲",
        "学号：TEST20260719001",
        "联系电话：13900000000",
        "邮箱：test.student@example.com",
        "身份证号：11010519491231002X",
    ],
    "handwriting_sensitive_spaced.png": [
        "2. 结合实际谈谈实践的作用。",
        "姓名：测试乙",
        "学号：202615001",
        "电话：138 0013 8000",
        "邮箱：tester@example.com",
    ],
    "handwriting_non_sensitive.png": [
        "3. 请阐释矛盾的普遍性与特殊性。",
        "我认为应当从具体历史条件出发分析问题。",
        "2026 年的课程学习使我更加理解实践观点。",
    ],
}


def _draw_handwritten_page(lines: list[str], seed: int) -> Image.Image:
    random = Random(seed)
    canvas = Image.new("RGB", (1800, 2200), "#fffef9")
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.truetype(str(FONT_PATH), 58)
    body_font = ImageFont.truetype(str(FONT_PATH), 52)

    draw.line((100, 120, 1700, 120), fill="#d2d0ca", width=2)
    y = 210
    for index, line in enumerate(lines):
        font = title_font if index == 0 else body_font
        x = 140 + random.randint(-10, 12)
        baseline = y + random.randint(-5, 5)
        ink = (18 + random.randint(0, 20), 25 + random.randint(0, 20), 45 + random.randint(0, 20))
        draw.text((x, baseline), line, font=font, fill=ink, stroke_width=0)
        y += 150 + random.randint(-8, 8)

    for line_y in range(180, 2050, 150):
        draw.line((100, line_y, 1700, line_y), fill="#e6e4df", width=1)
    return canvas.rotate(random.uniform(-0.55, 0.55), resample=Image.Resampling.BICUBIC, fillcolor="#fffef9")


def main() -> None:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"Chinese font not found: {FONT_PATH}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for index, (name, lines) in enumerate(SAMPLES.items(), start=1):
        _draw_handwritten_page(lines, seed=20260719 + index).save(OUTPUT_DIR / name)
    print(OUTPUT_DIR)
    for path in sorted(OUTPUT_DIR.glob("*.png")):
        print(path.name)


if __name__ == "__main__":
    main()
