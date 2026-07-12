from __future__ import annotations

import argparse
import mimetypes
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from template_builder.service import build_template_draft


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a reviewable answer-sheet template draft")
    parser.add_argument("path", help="Blank answer-sheet PDF/JPG/PNG")
    parser.add_argument("--template-id", required=True)
    parser.add_argument("--template-name", required=True)
    parser.add_argument("--exam-id", required=True, help="Exam whose saved question catalog defines canonical question_id values")
    parser.add_argument("--version", type=int, required=True, help="Positive immutable template version")
    args = parser.parse_args()
    source = Path(args.path)
    if not source.is_file():
        raise FileNotFoundError(source)
    mime_type, _ = mimetypes.guess_type(str(source))
    if not mime_type:
        raise ValueError(f"Cannot infer MIME type: {source}")
    template = build_template_draft(
        args.template_id, args.template_name, source, mime_type, args.version, args.exam_id,
    )
    print(f"Template draft created: {template['template_id']}")
    print("Status: pending_review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
