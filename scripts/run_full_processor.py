from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from full_pipeline import process_file_to_question_results


SUPPORTED_EXTS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _mime_type(path: Path) -> str:
    if path.suffix.lower() in SUPPORTED_EXTS:
        return SUPPORTED_EXTS[path.suffix.lower()]
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed:
        return guessed
    raise ValueError(f"不支持的文件类型：{path}")


def _load_optional_list(path_value: str | None) -> list[dict]:
    if not path_value:
        return []
    payload = json.loads(Path(path_value).read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise ValueError(f"{path_value} 顶层必须是 JSON 数组")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="完整文件处理入口：文件 -> OCR -> 题目级 JSON")
    parser.add_argument("path", help="PDF / DOCX / JPG / PNG 文件路径")
    parser.add_argument("--submission-id", default="sub_001")
    parser.add_argument("--assignment-type", default="homework")
    parser.add_argument("--exam-id", default=None, help="Server-side bound exam ID for a fixed answer sheet")
    parser.add_argument("--document-role", choices=["question_paper", "answer_sheet"], default="question_paper")
    parser.add_argument("--template-id", default=None)
    parser.add_argument("--question-regions-json", default=None)
    parser.add_argument("--review-results-json", default=None)
    parser.add_argument("--llm-enabled", action="store_true")
    parser.add_argument("--include-intermediate", action="store_true")
    parser.add_argument("--out", default=None, help="默认：<原文件名>_final_result.json")
    args = parser.parse_args()

    source = Path(args.path)
    if not source.is_file():
        raise FileNotFoundError(f"文件不存在：{source}")
    output_path = Path(args.out) if args.out else Path(f"{source.stem}_final_result.json")

    result = process_file_to_question_results(
        submission_id=args.submission_id,
        origin_name=source.name,
        mime_type=_mime_type(source),
        file_size=source.stat().st_size,
        source_path=source,
        assignment_type=args.assignment_type,
        template_id=args.template_id,
        question_regions=_load_optional_list(args.question_regions_json),
        review_results=_load_optional_list(args.review_results_json),
        llm_enabled=args.llm_enabled,
        include_intermediate=args.include_intermediate,
        exam_id=args.exam_id,
        document_role=args.document_role,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"处理完成：{source}")
    print(f"最终结果：{output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
