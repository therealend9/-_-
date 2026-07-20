from __future__ import annotations

"""Fine-tune the Open Model Zoo handwriting recognizer from its IR weights.

The IR is inference-only, so this reconstructs the published CNN/SE/CTC
architecture in PyTorch and imports convolution, projection, and bias
constants from the OpenVINO model before training. The script aborts before
training if the reconstructed model does not match the IR output.
"""

import argparse
import json
import random
from pathlib import Path

import cv2
import numpy as np
import openvino as ov
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset


class OpenVinoHandwritingNet(nn.Module):
    def __init__(self, model_path: Path):
        super().__init__()
        self.ov_model = ov.Core().read_model(str(model_path))
        self.nodes = {node.get_friendly_name(): node for node in self.ov_model.get_ordered_ops()}

        def conv(name: str) -> nn.Conv2d:
            node = self.nodes[name]
            weight = np.asarray(node.input_value(1).get_node().get_vector(), dtype=np.float32).reshape(node.input_value(1).get_shape())
            layer = nn.Conv2d(weight.shape[1], weight.shape[0], weight.shape[2:], padding=1 if weight.shape[2] == 3 else 0, bias=False)
            layer.weight = nn.Parameter(torch.from_numpy(weight.copy()))
            return layer

        def bias(name: str, channels: int) -> nn.Parameter:
            node = self.nodes[name]
            value = np.asarray(node.input_value(1).get_node().get_vector(), dtype=np.float32).reshape(1, channels, 1, 1)
            return nn.Parameter(torch.from_numpy(value.copy()))

        def linear(name: str) -> nn.Linear:
            node = self.nodes[name]
            weight = np.asarray(node.input_value(1).get_node().get_vector(), dtype=np.float32).reshape(node.input_value(1).get_shape())
            layer = nn.Linear(weight.shape[1], weight.shape[0], bias=False)
            layer.weight = nn.Parameter(torch.from_numpy(weight.copy()))
            return layer

        self.subtract = float(np.asarray(self.nodes["Constant_3826"].get_vector())[0])
        self.c11, self.c12 = conv("Multiply_3430"), conv("Multiply_3440")
        self.b11, self.b12 = bias("BatchNormalization_1", 64), bias("BatchNormalization_4", 64)
        self.c21, self.c22, self.c2skip, self.c23 = conv("Multiply_3450"), conv("Multiply_3460"), conv("Multiply_3467"), conv("Multiply_3477")
        self.b21, self.b22, self.b2skip, self.b23 = bias("BatchNormalization_8", 128), bias("BatchNormalization_11", 128), bias("BatchNormalization_35", 128), bias("BatchNormalization_39", 128)
        self.s21a, self.s21b = linear("MatMul_23"), linear("MatMul_25")
        self.c31, self.c32, self.c3skip, self.c33 = conv("Multiply_3487"), conv("Multiply_3497"), conv("Multiply_3504"), conv("Multiply_3514")
        self.b31, self.b32, self.b3skip, self.b33 = bias("BatchNormalization_43", 256), bias("BatchNormalization_46", 256), bias("BatchNormalization_70", 256), bias("BatchNormalization_74", 256)
        self.s31a, self.s31b = linear("MatMul_58"), linear("MatMul_60")
        self.c41, self.c42, self.c4skip, self.c43 = conv("Multiply_3524"), conv("Multiply_3534"), conv("Multiply_3541"), conv("Multiply_3551")
        self.b41, self.b42, self.b4skip, self.b43 = bias("BatchNormalization_78", 512), bias("BatchNormalization_81", 512), bias("BatchNormalization_105", 512), bias("BatchNormalization_109", 512)
        self.s41a, self.s41b = linear("MatMul_93"), linear("MatMul_95")
        self.c51, self.c52, self.c53 = conv("Multiply_3561"), conv("Multiply_3571"), conv("Multiply_3581")
        self.b51, self.b52, self.b53 = bias("BatchNormalization_113", 512), bias("BatchNormalization_116", 512), bias("BatchNormalization_142", 512)
        self.s51a, self.s51b = linear("MatMul_128"), linear("MatMul_130")
        final_node = self.nodes["MatMul_148"]
        final_weight = np.asarray(final_node.input_value(1).get_node().get_vector(), dtype=np.float32).reshape(final_node.input_value(1).get_shape())
        self.final = nn.Linear(final_weight.shape[1], final_weight.shape[0], bias=False)
        self.final.weight = nn.Parameter(torch.from_numpy(final_weight.copy()))
        final_bias = np.asarray(self.nodes["Add_149"].input_value(1).get_node().get_vector(), dtype=np.float32).reshape(1, 1, -1)
        self.final_bias = nn.Parameter(torch.from_numpy(final_bias.copy()))

    @staticmethod
    def _se(value: torch.Tensor, first: nn.Linear, second: nn.Linear) -> torch.Tensor:
        pooled = value.mean(dim=(2, 3))
        gate = torch.sigmoid(second(torch.relu(first(pooled))))
        return value * gate[:, :, None, None]

    @staticmethod
    def _add_bias(value: torch.Tensor, bias: nn.Parameter) -> torch.Tensor:
        return value + bias

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        value = value - self.subtract
        value = torch.relu(self._add_bias(self.c11(value), self.b11))
        value = torch.relu(self._add_bias(self.c12(value), self.b12))
        value = nn.functional.max_pool2d(value, 2, 2)

        residual = value
        value = torch.relu(self._add_bias(self.c21(value), self.b21))
        value = self._add_bias(self.c22(value), self.b22)
        value = self._se(value, self.s21a, self.s21b)
        skip = self._add_bias(self.c2skip(residual), self.b2skip)
        value = torch.relu(value + skip)
        value = torch.relu(self._add_bias(self.c23(value), self.b23))
        value = nn.functional.max_pool2d(value, 2, 2)

        residual = value
        value = torch.relu(self._add_bias(self.c31(value), self.b31))
        value = self._add_bias(self.c32(value), self.b32)
        value = self._se(value, self.s31a, self.s31b)
        skip = self._add_bias(self.c3skip(residual), self.b3skip)
        value = torch.relu(value + skip)
        value = torch.relu(self._add_bias(self.c33(value), self.b33))
        value = nn.functional.max_pool2d(value, 2, 2)

        residual = value
        value = torch.relu(self._add_bias(self.c41(value), self.b41))
        value = self._add_bias(self.c42(value), self.b42)
        value = self._se(value, self.s41a, self.s41b)
        skip = self._add_bias(self.c4skip(residual), self.b4skip)
        value = torch.relu(value + skip)
        value = torch.relu(self._add_bias(self.c43(value), self.b43))
        value = nn.functional.max_pool2d(value, 2, 2)

        residual = value
        value = torch.relu(self._add_bias(self.c51(value), self.b51))
        value = self._add_bias(self.c52(value), self.b52)
        value = self._se(value, self.s51a, self.s51b)
        value = torch.relu(value + residual)
        value = torch.relu(self._add_bias(self.c53(value), self.b53))
        value = nn.functional.max_pool2d(value, 2, 2)

        value = value.reshape(value.shape[0], 512, -1).transpose(1, 2)
        return (self.final(value) + self.final_bias).transpose(0, 1)


class CasiaDataset(Dataset):
    def __init__(self, manifest: Path, charset: set[str], limit: int):
        self.manifest_root = manifest.parent.parent
        self.items = []
        for line in manifest.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["text"] in charset:
                self.items.append(item)
            if limit and len(self.items) >= limit:
                break

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        item = self.items[index]
        image_path = self.manifest_root / item["image"]
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        canvas = np.full((96, 2000), 255, dtype=np.float32)
        image = cv2.resize(image, (96, 96), interpolation=cv2.INTER_CUBIC)
        canvas[:, :96] = image
        return torch.from_numpy(canvas[None]), item["text"]


class CasiaSyntheticLineDataset(Dataset):
    def __init__(self, manifest: Path, charset: set[str], length: int, seed: int = 20260716):
        self.root = manifest.parent.parent
        self.pools: dict[str, list[Path]] = {}
        for line in manifest.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item["text"] in charset:
                self.pools.setdefault(item["text"], []).append(self.root / item["image"])
        self.labels = sorted(self.pools)
        self.length = length
        self.seed = seed

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        rng = random.Random(self.seed + index)
        target = "".join(rng.choice(self.labels) for _ in range(rng.randint(2, 8)))
        canvas = np.full((96, 2000), 255, dtype=np.float32)
        x = rng.randint(8, 24)
        for char in target:
            image = cv2.imread(str(rng.choice(self.pools[char])), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            ys, xs = np.where(image < 245)
            if len(xs):
                image = image[max(0, ys.min() - 3):min(image.shape[0], ys.max() + 4), max(0, xs.min() - 3):min(image.shape[1], xs.max() + 4)]
            scale = rng.uniform(0.78, 1.0)
            height = max(42, min(82, round(image.shape[0] * scale)))
            width = max(24, round(image.shape[1] * height / max(1, image.shape[0])))
            image = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
            if x + width >= 1980:
                break
            top = rng.randint(7, max(7, 89 - height))
            canvas[top:top + height, x:x + width] = np.minimum(canvas[top:top + height, x:x + width], image)
            x += width + rng.randint(8, 24)
        return torch.from_numpy(canvas[None]), target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--charset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--synthetic-lines", action="store_true")
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    charset_list = args.charset.read_text(encoding="utf-8").splitlines()
    charset = set(charset_list)
    model = OpenVinoHandwritingNet(args.model).eval()
    sample = torch.zeros((1, 1, 96, 2000), dtype=torch.float32)
    core = ov.Core()
    compiled = core.compile_model(str(args.model), "CPU")
    reference = compiled([sample.numpy()])[compiled.output(0)]
    with torch.no_grad():
        recreated = model(sample).numpy()
    max_error = float(np.max(np.abs(reference - recreated)))
    (args.output / "reconstruction_check.json").write_text(json.dumps({"max_absolute_error": max_error, "reference_shape": list(reference.shape)}, indent=2), encoding="utf-8")
    if max_error > 1e-3:
        raise RuntimeError(f"Reconstructed model does not match OpenVINO IR; max error={max_error}")
    if args.resume:
        model.load_state_dict(torch.load(args.resume, map_location="cpu"))
    model.train()

    dataset = CasiaSyntheticLineDataset(args.train_manifest, charset, args.limit) if args.synthetic_lines else CasiaDataset(args.train_manifest, charset, args.limit)
    loader = DataLoader(dataset, batch_size=1, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)
    loss_fn = nn.CTCLoss(blank=0, zero_infinity=True)
    # This first run is deliberately a short smoke fine-tune after the exact
    # reconstruction check; a longer run is only meaningful after it passes.
    history = []
    for step, (images, texts) in enumerate(loader):
        if step >= args.steps:
            break
        logits = model(images).log_softmax(2)
        target = texts[0]
        labels = torch.tensor([charset_list.index(char) + 1 for char in target], dtype=torch.long)
        loss = loss_fn(logits, labels, torch.tensor([logits.shape[0]]), torch.tensor([len(target)]))
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        history.append({"step": step + 1, "loss": float(loss.detach())})
    torch.save(model.state_dict(), args.output / "openvino_reconstructed_finetuned.pt")
    (args.output / "training_summary.json").write_text(json.dumps({"dataset": "CASIA-OLHWDB1.1", "steps": len(history), "history": history}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
