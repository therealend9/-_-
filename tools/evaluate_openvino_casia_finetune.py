from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from finetune_openvino_handwriting_casia import CasiaDataset, CasiaSyntheticLineDataset, OpenVinoHandwritingNet


def distance(first: str, second: str) -> int:
    previous = list(range(len(second) + 1))
    for row, left in enumerate(first, 1):
        current = [row]
        for column, right in enumerate(second, 1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


@torch.no_grad()
def evaluate(model, dataset, charset_list: list[str], limit: int) -> dict:
    loader = DataLoader(dataset, batch_size=1, shuffle=False)
    total = errors = exact = 0
    examples = []
    model.eval()
    for images, texts in loader:
        if total >= limit:
            break
        logits = model(images)
        indices = logits[:, 0, :].argmax(dim=1).tolist()
        decoded = []
        previous = -1
        for index in indices:
            if index and index != previous and index - 1 < len(charset_list):
                decoded.append(charset_list[index - 1])
            previous = index
        predicted = "".join(decoded)
        expected = texts[0]
        errors += distance(expected, predicted)
        exact += int(expected == predicted)
        total += len(expected)
        if len(examples) < 20:
            examples.append({"expected": expected, "predicted": predicted})
    return {"samples": total, "character_error_rate": round(errors / max(1, total), 6), "exact_accuracy": round(exact / max(1, len(dataset)), 6), "examples": examples}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--finetuned", type=Path, required=True)
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--charset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--synthetic-lines", action="store_true")
    args = parser.parse_args()
    charset_list = args.charset.read_text(encoding="utf-8").splitlines()
    charset = set(charset_list)
    dataset = CasiaSyntheticLineDataset(args.test_manifest, charset, args.limit, seed=20260717) if args.synthetic_lines else CasiaDataset(args.test_manifest, charset, args.limit)
    baseline = OpenVinoHandwritingNet(args.model)
    tuned = OpenVinoHandwritingNet(args.model)
    tuned.load_state_dict(torch.load(args.finetuned, map_location="cpu"))
    result = {"dataset": "CASIA-OLHWDB1.1 official test archive", "limit": args.limit, "baseline": evaluate(baseline, dataset, charset_list, args.limit), "finetuned": evaluate(tuned, dataset, charset_list, args.limit)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
