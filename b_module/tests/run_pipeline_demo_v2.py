from __future__ import annotations

import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from b_module.demo.service import format_demo_summary, run_demo_case


MOCK_DIR = BASE_DIR / "mock_data"


def load_case(filename: str) -> dict:
    with (MOCK_DIR / filename).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def run_case(filename: str) -> dict:
    case = load_case(filename)
    return run_demo_case(case)


def main() -> None:
    filenames = [
        "free_layout_case_basic.json",
        "free_layout_case_cross_page.json",
        "free_layout_case_multi_page_complex_a.json",
        "free_layout_case_multi_page_complex_b.json",
    ]
    for filename in filenames:
        result = run_case(filename)
        print(f"=== {filename} ===")
        print(json.dumps(format_demo_summary(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
