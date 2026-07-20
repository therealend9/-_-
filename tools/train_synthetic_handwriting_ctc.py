from __future__ import annotations

import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
import paddle
from paddle.io import DataLoader, Dataset


DATA_DIR = ROOT / "test_artifacts" / "public_licensed_handwriting_20260716" / "extracted_part001"
CASIA_DIR = Path(os.getenv("CASIA_RASTER_DATASET_DIR", "")) if os.getenv("CASIA_RASTER_DATASET_DIR") else None
CHARSET_PATH = ROOT / "third_party" / "openvino_models" / "intel" / "handwritten-simplified-chinese-recognition-0001" / "scut_ept_charset.txt"
OUTPUT_DIR = Path(os.getenv("SYNTHETIC_CTC_OUTPUT_DIR", str(ROOT / "test_artifacts" / "experimental_handwriting_finetune_20260716")))
HEIGHT, WIDTH = 64, 512
EPOCHS = int(os.getenv("SYNTHETIC_CTC_EPOCHS", "3"))
STEPS_PER_EPOCH = int(os.getenv("SYNTHETIC_CTC_STEPS_PER_EPOCH", "250"))
BATCH_SIZE = int(os.getenv("SYNTHETIC_CTC_BATCH_SIZE", "16"))
VALIDATION_SAMPLES = int(os.getenv("SYNTHETIC_CTC_VALIDATION_SAMPLES", "300"))
MAX_CHARS = 8


def ctc_decode(logits: np.ndarray, id_to_char: dict[int, str]) -> str:
    indices = logits.argmax(axis=1).tolist()
    result: list[str] = []
    previous = -1
    for index in indices:
        if index and index != previous:
            result.append(id_to_char[index])
        previous = index
    return "".join(result)


def edit_distance(first: str, second: str) -> int:
    previous = list(range(len(second) + 1))
    for row, left in enumerate(first, start=1):
        current = [row]
        for column, right in enumerate(second, start=1):
            current.append(min(current[-1] + 1, previous[column] + 1, previous[column - 1] + (left != right)))
        previous = current
    return previous[-1]


def build_pools() -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    charset = set(CHARSET_PATH.read_text(encoding="utf-8").splitlines())
    grouped: dict[str, list[Path]] = defaultdict(list)
    if CASIA_DIR:
        for split in ("train", "test"):
            manifest = CASIA_DIR / split / "labels.jsonl"
            if not manifest.is_file():
                continue
            target = grouped if split == "train" else None
            # Keep the test pool separate so validation never reuses train strokes.
            pool = defaultdict(list)
            for raw in manifest.read_text(encoding="utf-8").splitlines():
                item = json.loads(raw)
                if item["text"] in charset:
                    pool[item["text"]].append(CASIA_DIR / item["image"])
            if split == "train":
                train = dict(pool)
            else:
                valid = dict(pool)
        labels = sorted(set(train) & set(valid))
        return {key: train[key] for key in labels}, {key: valid[key] for key in labels}
    for path in DATA_DIR.rglob("*.png"):
        label = path.stem.rsplit("_", 1)[0]
        if label in charset:
            grouped[label].append(path)
    train, valid = {}, {}
    for label, paths in grouped.items():
        paths.sort(key=lambda item: item.name)
        cut = max(1, int(len(paths) * 0.9))
        if cut == len(paths):
            cut -= 1
        train[label], valid[label] = paths[:cut], paths[cut:]
    return train, valid


class SyntheticLineDataset(Dataset):
    def __init__(self, pools: dict[str, list[Path]], label_to_id: dict[str, int], length: int, seed: int) -> None:
        self.pools = pools
        self.labels = sorted(pools)
        self.label_to_id = label_to_id
        self.length = length
        self.seed = seed

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int):
        rng = random.Random(self.seed + index)
        count = rng.randint(2, MAX_CHARS)
        text = [rng.choice(self.labels) for _ in range(count)]
        tiles = []
        for char in text:
            data = np.fromfile(str(rng.choice(self.pools[char])), dtype=np.uint8)
            image = cv2.imdecode(data, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError("Cannot read dataset image")
            scale = rng.uniform(0.88, 1.08)
            tile_height = max(36, min(62, int(54 * scale)))
            tile_width = max(22, int(image.shape[1] * tile_height / image.shape[0]))
            tile = cv2.resize(image, (tile_width, tile_height), interpolation=cv2.INTER_CUBIC)
            top = rng.randint(1, max(1, HEIGHT - tile_height - 1))
            tiles.append((top, tile))
        canvas = np.full((HEIGHT, WIDTH), 255, dtype=np.uint8)
        x = rng.randint(2, 10)
        for top, tile in tiles:
            if x + tile.shape[1] >= WIDTH - 2:
                break
            canvas[top:top + tile.shape[0], x:x + tile.shape[1]] = np.minimum(
                canvas[top:top + tile.shape[0], x:x + tile.shape[1]], tile
            )
            x += tile.shape[1] + rng.randint(2, 9)
        return canvas.astype("float32")[None, :, :] / 255.0, np.asarray([self.label_to_id[item] for item in text], dtype="int32")


def collate(batch):
    images = np.stack([item[0] for item in batch])
    labels = [item[1] for item in batch]
    max_len = max(len(item) for item in labels)
    padded = np.zeros((len(labels), max_len), dtype="int32")
    lengths = np.zeros((len(labels),), dtype="int64")
    for index, item in enumerate(labels):
        padded[index, :len(item)] = item
        lengths[index] = len(item)
    return images, padded, lengths


class CRNN(paddle.nn.Layer):
    def __init__(self, class_count: int) -> None:
        super().__init__()
        self.features = paddle.nn.Sequential(
            paddle.nn.Conv2D(1, 32, 3, padding=1), paddle.nn.ReLU(), paddle.nn.MaxPool2D(2, 2),
            paddle.nn.Conv2D(32, 64, 3, padding=1), paddle.nn.ReLU(), paddle.nn.MaxPool2D(2, 2),
            paddle.nn.Conv2D(64, 128, 3, padding=1), paddle.nn.ReLU(), paddle.nn.MaxPool2D((2, 1), (2, 1)),
            paddle.nn.Conv2D(128, 128, 3, padding=1), paddle.nn.ReLU(),
        )
        self.rnn = paddle.nn.GRU(128, 128, direction="bidirectional")
        self.head = paddle.nn.Linear(256, class_count)

    def forward(self, image):
        value = self.features(image)
        value = paddle.mean(value, axis=2).transpose([0, 2, 1])
        value, _ = self.rnn(value)
        return self.head(value)


@paddle.no_grad()
def evaluate(model, loader, id_to_char: dict[int, str]) -> dict[str, float]:
    model.eval()
    distances, total_chars, exact, count = 0, 0, 0, 0
    for images, labels, label_lengths in loader:
        logits = model(paddle.to_tensor(images)).numpy()
        label_values = labels.numpy() if hasattr(labels, "numpy") else labels
        length_values = label_lengths.numpy() if hasattr(label_lengths, "numpy") else label_lengths
        for index in range(len(label_values)):
            predicted = ctc_decode(logits[index], id_to_char)
            expected = "".join(id_to_char[int(value)] for value in label_values[index, :length_values[index]])
            distances += edit_distance(expected, predicted)
            total_chars += len(expected)
            exact += int(expected == predicted)
            count += 1
    return {"character_error_rate": round(distances / max(1, total_chars), 4), "exact_line_accuracy": round(exact / max(1, count), 4)}


def main() -> None:
    paddle.set_device("cpu")
    paddle.seed(20260716)
    np.random.seed(20260716)
    random.seed(20260716)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_pools, valid_pools = build_pools()
    labels = sorted(set(train_pools) & set(valid_pools))
    train_pools = {key: train_pools[key] for key in labels}
    valid_pools = {key: valid_pools[key] for key in labels}
    label_to_id = {label: index for index, label in enumerate(labels, start=1)}
    id_to_char = {index: label for label, index in label_to_id.items()}
    train_ds = SyntheticLineDataset(train_pools, label_to_id, STEPS_PER_EPOCH * BATCH_SIZE, 1000)
    valid_ds = SyntheticLineDataset(valid_pools, label_to_id, VALIDATION_SAMPLES, 900000)
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, collate_fn=collate)
    valid_loader = DataLoader(valid_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0, collate_fn=collate)
    model = CRNN(len(labels) + 1)
    optimizer = paddle.optimizer.Adam(learning_rate=0.001, parameters=model.parameters())
    loss_fn = paddle.nn.CTCLoss(blank=0, reduction="mean")
    history = []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        loss_sum, batches = 0.0, 0
        for images, labels_batch, label_lengths in train_loader:
            logits = model(paddle.to_tensor(images)).transpose([1, 0, 2])
            input_lengths = paddle.full([logits.shape[1]], logits.shape[0], dtype="int64")
            loss = loss_fn(logits, labels_batch.astype("int32"), input_lengths, label_lengths.astype("int64"))
            loss.backward()
            optimizer.step()
            optimizer.clear_grad()
            loss_sum += float(loss.numpy())
            batches += 1
        metrics = evaluate(model, valid_loader, id_to_char)
        history.append({"epoch": epoch, "train_loss": round(loss_sum / max(1, batches), 4), **metrics})
        paddle.save(model.state_dict(), str(OUTPUT_DIR / "synthetic_ctc_latest.pdparams"))
    summary = {
        "dataset": "CASIA-OLHWDB1.1 rasterized character images" if CASIA_DIR else "AI-FREE-Team Traditional Chinese Handwriting Dataset, CC BY-SA 4.0",
        "training_type": "Synthetic multi-character line CTC training from isolated character images",
        "source_mode": "CASIA official POT labels" if CASIA_DIR else "public isolated-character filenames",
        "device": "cpu",
        "class_count": len(labels),
        "train_samples_per_epoch": len(train_ds),
        "validation_samples": len(valid_ds),
        "history": history,
        "limitations": "This is an experimental candidate trained on synthetic lines and a subset of characters shared with the simplified-Chinese charset. It is not a replacement for the OpenVINO answer-sheet recognizer without natural-line evaluation.",
    }
    (OUTPUT_DIR / "training_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
