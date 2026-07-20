from __future__ import annotations

"""Prepare CASIA-OLHWDB samples as labeled raster images.

CASIA-OLHWDB is an online handwriting dataset. This utility rasterizes the
officially labeled stroke sequences so they can be used for character
pretraining and controlled synthetic-line experiments. It deliberately keeps
the official train/test archive split and never creates labels by OCR.
"""

import argparse
import json
import struct
import zipfile
from pathlib import Path

import cv2
import numpy as np


HEADER_SIZE = 8


def read_pot_samples(path: Path):
    with path.open("rb") as stream:
        while True:
            header = stream.read(HEADER_SIZE)
            if len(header) < HEADER_SIZE:
                return
            sample_size, tag, stroke_count = struct.unpack("<H4sH", header)
            if tag[0]:
                codepoint = (tag[1] << 8) | tag[0]
                width = 2
            else:
                codepoint = tag[1]
                width = 1
            try:
                label = codepoint.to_bytes(width, "big").decode("gbk")
            except UnicodeDecodeError:
                stream.seek(sample_size - HEADER_SIZE, 1)
                continue

            strokes = []
            for _ in range(stroke_count):
                stroke = []
                while True:
                    point = stream.read(4)
                    if len(point) < 4:
                        return
                    x, y = struct.unpack("<hh", point)
                    if x == -1 and y == 0:
                        break
                    stroke.append((x, y))
                strokes.append(stroke)

            # POT records include an additional end marker after all strokes.
            stream.read(4)
            yield label, strokes


def render(strokes: list[list[tuple[int, int]]], size: int = 96) -> np.ndarray | None:
    points = [point for stroke in strokes for point in stroke]
    if not points:
        return None
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    padding = 8
    width = max(1, max_x - min_x + padding * 2)
    height = max(1, max_y - min_y + padding * 2)
    canvas = np.full((height, width), 255, dtype=np.uint8)
    for stroke in strokes:
        if len(stroke) < 2:
            continue
        points_array = np.asarray(
            [[x - min_x + padding, y - min_y + padding] for x, y in stroke],
            dtype=np.int32,
        )
        cv2.polylines(canvas, [points_array], False, 0, thickness=2, lineType=cv2.LINE_AA)
    scale = min((size - 8) / canvas.shape[0], (size - 8) / canvas.shape[1])
    scaled = cv2.resize(canvas, (max(1, round(canvas.shape[1] * scale)), max(1, round(canvas.shape[0] * scale))), interpolation=cv2.INTER_AREA)
    output = np.full((size, size), 255, dtype=np.uint8)
    top = (size - scaled.shape[0]) // 2
    left = (size - scaled.shape[1]) // 2
    output[top:top + scaled.shape[0], left:left + scaled.shape[1]] = scaled
    return output


def process_archive(archive: Path, output_dir: Path, split: str, limit: int) -> dict:
    image_dir = output_dir / split / "characters"
    image_dir.mkdir(parents=True, exist_ok=True)
    manifest = output_dir / split / "labels.jsonl"
    count = 0
    classes: set[str] = set()
    with zipfile.ZipFile(archive) as zf, manifest.open("w", encoding="utf-8") as labels:
        for member in zf.namelist():
            if not member.lower().endswith(".pot"):
                continue
            temporary = output_dir / "_current.pot"
            temporary.write_bytes(zf.read(member))
            samples = read_pot_samples(temporary)
            for local_index, (label, strokes) in enumerate(samples):
                image = render(strokes)
                if image is None:
                    continue
                sample_id = f"{split}_{count:07d}"
                image_path = image_dir / f"{sample_id}.png"
                cv2.imwrite(str(image_path), image)
                labels.write(json.dumps({"image": str(image_path.relative_to(output_dir)), "text": label, "source": member}, ensure_ascii=False) + "\n")
                classes.add(label)
                count += 1
                if limit and count >= limit:
                    samples.close()
                    temporary.unlink(missing_ok=True)
                    return {"split": split, "samples": count, "classes": len(classes), "archive": str(archive)}
            samples.close()
            temporary.unlink(missing_ok=True)
    return {"split": split, "samples": count, "classes": len(classes), "archive": str(archive)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-zip", type=Path, required=True)
    parser.add_argument("--test-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-limit", type=int, default=20000)
    parser.add_argument("--test-limit", type=int, default=5000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {
        "dataset": "CASIA-OLHWDB1.1",
        "label_source": "official POT character tags",
        "rendering": "stroke rasterization to 96x96 grayscale PNG",
        "splits": [
            process_archive(args.train_zip, args.output, "train", args.train_limit),
            process_archive(args.test_zip, args.output, "test", args.test_limit),
        ],
        "note": "This is character-level data, not transcribed answer lines. It must not be reported as end-to-end answer-sheet accuracy.",
    }
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
