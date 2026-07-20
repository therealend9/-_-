from __future__ import annotations

import argparse
from pathlib import Path

import openvino as ov
import torch

from finetune_openvino_handwriting_casia import OpenVinoHandwritingNet


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = OpenVinoHandwritingNet(args.base_model)
    model.load_state_dict(torch.load(args.checkpoint, map_location="cpu"))
    model.eval()
    converted = ov.convert_model(model, example_input=torch.zeros((1, 1, 96, 2000), dtype=torch.float32))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ov.save_model(converted, str(args.output))
    print({"xml": str(args.output), "outputs": [str(output.get_partial_shape()) for output in converted.outputs]})


if __name__ == "__main__":
    main()
