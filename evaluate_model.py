"""
PURPOSE: Evaluate a Teachable Machine image-classification model using labelled test images.
HOW TO RUN:
    python evaluate_model.py --test-dir dataset/test_images
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from src.sign_model import SignLanguageModel


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def normalise_label(value: str) -> str:
    """Make folder names and labels.txt names easier to match."""
    value = value.strip().lower()
    value = re.sub(r"^\d+\s+", "", value)
    value = value.replace("_", " ").replace("-", " ")
    return " ".join(value.split())


def find_label_index(folder_name: str, labels: list[str]) -> int | None:
    wanted = normalise_label(folder_name)
    for index, label in enumerate(labels):
        if normalise_label(label) == wanted:
            return index
    return None


def load_rgb_image(path: Path) -> np.ndarray | None:
    """Read an image safely, including paths containing non-ASCII characters."""
    try:
        encoded = np.fromfile(str(path), dtype=np.uint8)
        frame_bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except Exception:
        return None

    if frame_bgr is None:
        return None

    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)


def collect_test_images(
    test_dir: Path, labels: list[str]
) -> tuple[list[tuple[Path, int]], list[str]]:
    samples: list[tuple[Path, int]] = []
    warnings: list[str] = []

    if not test_dir.exists():
        raise FileNotFoundError(
            f"Test folder not found: {test_dir}\n"
            "Create one folder per class inside test_images."
        )

    for class_folder in sorted(p for p in test_dir.iterdir() if p.is_dir()):
        label_index = find_label_index(class_folder.name, labels)

        if label_index is None:
            warnings.append(
                f'Ignored folder "{class_folder.name}" because it does not match '
                "any label in labels.txt."
            )
            continue

        image_paths = sorted(
            p for p in class_folder.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )

        if not image_paths:
            warnings.append(f'No supported images found in "{class_folder}".')

        samples.extend((path, label_index) for path in image_paths)

    return samples, warnings


def save_confusion_matrix(
    matrix: np.ndarray, labels: list[str], output_path: Path
) -> None:
    figure_size = max(8, len(labels) * 1.15)
    fig, ax = plt.subplots(figsize=(figure_size, figure_size))

    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax)

    positions = np.arange(len(labels))
    ax.set(
        xticks=positions,
        yticks=positions,
        xticklabels=labels,
        yticklabels=labels,
        xlabel="Predicted label",
        ylabel="Actual label",
        title="Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    threshold = matrix.max() / 2 if matrix.size and matrix.max() else 0
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            ax.text(
                column,
                row,
                str(matrix[row, column]),
                ha="center",
                va="center",
                color="white" if matrix[row, column] > threshold else "black",
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_predictions_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    fieldnames = [
        "image",
        "actual_label",
        "predicted_label",
        "confidence",
        "correct",
    ]
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate(test_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading Teachable Machine model...")
    model = SignLanguageModel()
    labels = model.labels

    samples, warnings = collect_test_images(test_dir, labels)
    for warning in warnings:
        print(f"WARNING: {warning}")

    if not samples:
        raise RuntimeError(
            "No valid test images were found. Ensure folder names match labels.txt."
        )

    y_true: list[int] = []
    y_pred: list[int] = []
    prediction_rows: list[dict[str, object]] = []
    skipped = 0

    print(f"Testing {len(samples)} image(s)...")

    for number, (image_path, true_index) in enumerate(samples, start=1):
        frame_rgb = load_rgb_image(image_path)
        if frame_rgb is None:
            print(f"WARNING: Could not read {image_path}")
            skipped += 1
            continue

        predicted_label, confidence, ranked = model.predict(frame_rgb)
        predicted_index = max(
            range(len(ranked)),
            key=lambda i: ranked[i][1],
        )
        # ranked is sorted, so use the original labels list to obtain a stable index.
        predicted_index = labels.index(predicted_label)

        y_true.append(true_index)
        y_pred.append(predicted_index)

        prediction_rows.append(
            {
                "image": str(image_path),
                "actual_label": labels[true_index],
                "predicted_label": predicted_label,
                "confidence": f"{confidence:.6f}",
                "correct": true_index == predicted_index,
            }
        )

        print(
            f"[{number}/{len(samples)}] {image_path.name}: "
            f"actual={labels[true_index]} | predicted={predicted_label} "
            f"| confidence={confidence * 100:.2f}%"
        )

    if not y_true:
        raise RuntimeError("All test images failed to load.")

    all_indices = list(range(len(labels)))
    matrix = confusion_matrix(y_true, y_pred, labels=all_indices)
    accuracy = accuracy_score(y_true, y_pred)

    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=all_indices,
        average="macro",
        zero_division=0,
    )
    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=all_indices,
            average="weighted",
            zero_division=0,
        )
    )

    report_text = classification_report(
        y_true,
        y_pred,
        labels=all_indices,
        target_names=labels,
        digits=4,
        zero_division=0,
    )

    summary = (
        f"Total valid test images: {len(y_true)}\n"
        f"Skipped unreadable images: {skipped}\n\n"
        f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)\n\n"
        f"Macro Precision: {macro_precision:.4f}\n"
        f"Macro Recall:    {macro_recall:.4f}\n"
        f"Macro F1-score:  {macro_f1:.4f}\n\n"
        f"Weighted Precision: {weighted_precision:.4f}\n"
        f"Weighted Recall:    {weighted_recall:.4f}\n"
        f"Weighted F1-score:  {weighted_f1:.4f}\n\n"
        "Classification Report\n"
        "=====================\n"
        f"{report_text}"
    )

    print("\n" + summary)

    (output_dir / "metrics_report.txt").write_text(summary, encoding="utf-8")
    np.savetxt(
        output_dir / "confusion_matrix.csv",
        matrix,
        delimiter=",",
        fmt="%d",
        header=",".join(labels),
        comments="",
    )
    save_confusion_matrix(
        matrix, labels, output_dir / "confusion_matrix.png"
    )
    save_predictions_csv(
        prediction_rows, output_dir / "image_predictions.csv"
    )

    print(f"\nResults saved in: {output_dir.resolve()}")
    print("- metrics_report.txt")
    print("- confusion_matrix.png")
    print("- confusion_matrix.csv")
    print("- image_predictions.csv")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a Teachable Machine sign-language model."
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path("test_images"),
        help="Folder containing one subfolder per class.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("evaluation_results"),
        help="Folder where evaluation files will be saved.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()
    evaluate(arguments.test_dir, arguments.output_dir)
