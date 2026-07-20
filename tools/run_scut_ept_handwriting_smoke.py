from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from d_module.ocr_engine.service import run_ocr_on_page
from d_module.schemas.normalized_page import NormalizedPage

from benchmark_handwriting_preprocessing import make_variant, page_for


SAMPLE_DIR = ROOT / "test_artifacts" / "paddleocr_handwriting_20260716"
INPUT_DIR = SAMPLE_DIR / "scut_ept_unlabeled"
OUTPUT = SAMPLE_DIR / "scut_ept_smoke_results.json"


def main() -> None:
    images = sorted(INPUT_DIR.glob("*.jpg"))
    if len(images) < 30:
        raise ValueError(f"Expected 30 SCUT-EPT samples, found {len(images)}")
    output = {
        "source": "https://github.com/HCIILAB/SCUT-EPT_Dataset_Release",
        "sample_count": len(images),
        "limitation": "The public sample repository does not include per-image transcripts. This file records real inference outputs for qualitative comparison only; it is not an accuracy metric.",
        "variants": [],
    }
    for variant in ("original", "gray_upscale_2x"):
        records = []
        for source in images:
            image_path = make_variant(source, variant)
            page: NormalizedPage = page_for(f"scut_{variant}_{source.stem}", image_path)
            result = run_ocr_on_page(page.file_id, page)
            records.append(
                {
                    "image": source.name,
                    "predicted_text": "\n".join(block.text for block in result.blocks if block.text).strip(),
                    "confidence": result.overall_confidence or 0.0,
                    "block_count": len(result.blocks),
                }
            )
        output["variants"].append({"id": variant, "records": records})
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
