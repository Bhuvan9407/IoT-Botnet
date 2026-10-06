"""
Milestone 4 training and evaluation infrastructure.

Supports:
    1. Ensemble: Random Forest + Extra Trees + Gradient Boosting
    2. Autoencoder: unsupervised anomaly detection
    3. 1D-CNN: supervised classifier

Split protocols:
    random
    ldo (Leave-Device-Out)

Leakage rule:
    Input data comes from data/processed_unscaled.
    StandardScaler is fitted ONLY on the training split/fold.

Autoencoder rule:
    Trained ONLY on benign samples from the training split/fold.

Shared metrics:
    Accuracy
    Macro-F1
    FPR

FPR:
    FP / (FP + TN)

Labels:
    0 = benign
    1 = attack
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# IMPORTANT:
# Milestone 4 uses unscaled data so that scaling can be fitted only on
# training data for each split/fold.
PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed_unscaled"
)

RESULTS_DIR = PROJECT_ROOT / "results"

DEFAULT_RANDOM_STATE = 42
DEFAULT_TEST_SIZE = 0.20

DEFAULT_EPOCHS = 5
DEFAULT_BATCH_SIZE = 256

DEFAULT_AUTOENCODER_THRESHOLD_PERCENTILE = 95.0


# ---------------------------------------------------------------------------
# Python path
# ---------------------------------------------------------------------------

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Model imports
# ---------------------------------------------------------------------------

from src.models.ensemble import build_ensemble
from src.models.autoencoder import build_autoencoder
from src.models.cnn import build_cnn


# ---------------------------------------------------------------------------
# Dataset / LDO groups
# ---------------------------------------------------------------------------

NBAIOT_GROUPS = [
    "Danmini_Doorbell",
    "Ecobee_Thermostat",
    "Ennio_Doorbell",
    "Philips_B120N10_Baby_Monitor",
    "Provision_PT_737E_Security_Camera",
    "Provision_PT_838_Security_Camera",
    "Samsung_SNH_1011_N_Webcam",
    "SimpleHome_XCS7_1002_WHT_Security_Camera",
    "SimpleHome_XCS7_1003_WHT_Security_Camera",
]

MEDBIOT_GROUPS = [
    "fan",
    "light",
    "switch",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def filename_for_group(group_name: str) -> str:
    """Return the Milestone 4 unscaled filename for a group."""
    return f"{group_name}_unscaled.npy"


def load_processed_file(group_name: str):
    """
    Load one unscaled processed LDO unit.

    Expected shape:
        rows x 101

    First 100 columns:
        features

    Final column:
        binary label
    """

    filename = filename_for_group(group_name)
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {path}"
        )

    data = np.load(
        path,
        mmap_mode="r",
    )

    if data.ndim != 2:
        raise ValueError(
            f"Expected 2D array in {path}, "
            f"got {data.shape}"
        )

    if data.shape[1] != 101:
        raise ValueError(
            f"Expected 101 columns in {path}, "
            f"got {data.shape[1]}"
        )

    X = np.asarray(
        data[:, :100],
        dtype=np.float32,
    )

    y = np.asarray(
        data[:, 100],
        dtype=np.int8,
    )

    unique_labels = np.unique(y)

    if not np.all(
        np.isin(unique_labels, [0, 1])
    ):
        raise ValueError(
            f"Unexpected labels in {path}: "
            f"{unique_labels}"
        )

    if not np.isfinite(X).all():
        raise ValueError(
            f"Non-finite feature values detected in {path}"
        )

    return X, y


def load_groups(group_names):
    """Load and concatenate multiple LDO groups."""

    if not group_names:
        raise ValueError(
            "No dataset groups were supplied."
        )

    X_parts = []
    y_parts = []

    for group_name in group_names:
        X, y = load_processed_file(group_name)

        print(
            f"  Loaded {group_name}: "
            f"X={X.shape}, "
            f"benign={np.sum(y == 0):,}, "
            f"attack={np.sum(y == 1):,}"
        )

        X_parts.append(X)
        y_parts.append(y)

    X = np.concatenate(
        X_parts,
        axis=0,
    )

    y = np.concatenate(
        y_parts,
        axis=0,
    )

    return X, y


# ---------------------------------------------------------------------------
# Optional row caps
# ---------------------------------------------------------------------------

def cap_rows(
    X,
    y,
    max_rows,
    random_state,
    description,
):
    """
    Apply an optional stratified row cap.

    Used mainly for smoke tests.
    """

    if max_rows is None:
        return X, y

    if len(y) <= max_rows:
        return X, y

    if max_rows < 2:
        raise ValueError(
            "Row cap must be at least 2."
        )

    X_subset, _, y_subset, _ = train_test_split(
        X,
        y,
        train_size=max_rows,
        random_state=random_state,
        stratify=y,
    )

    print(
        f"  {description}: "
        f"{len(y):,} -> {len(y_subset):,} rows"
    )

    return X_subset, y_subset


# ---------------------------------------------------------------------------
# Split creation
# ---------------------------------------------------------------------------

def make_random_split(
    group_names,
    test_size,
    random_state,
    max_train_rows=None,
    max_test_rows=None,
):
    """Create a stratified random train/test split."""

    print()
    print("=" * 72)
    print("Creating random split")
    print("=" * 72)

    X, y = load_groups(group_names)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    X_train, y_train = cap_rows(
        X_train,
        y_train,
        max_train_rows,
        random_state,
        "Training cap",
    )

    X_test, y_test = cap_rows(
        X_test,
        y_test,
        max_test_rows,
        random_state,
        "Test cap",
    )

    return (
        X_train,
        y_train,
        X_test,
        y_test,
    )


def make_ldo_splits(
    group_names,
    fold=None,
    max_train_rows=None,
    max_test_rows=None,
    random_state=DEFAULT_RANDOM_STATE,
):
    """
    Create Leave-Device-Out splits.

    One complete group is held out as the test set.

    N-BaIoT:
        physical device

    MedBIoT:
        device type
    """

    if fold is not None:
        if fold not in group_names:
            raise ValueError(
                f"Unknown LDO fold '{fold}'. "
                f"Available groups: {group_names}"
            )

        test_groups = [fold]
    else:
        test_groups = list(group_names)

    splits = []

    for test_group in test_groups:
        train_groups = [
            group
            for group in group_names
            if group != test_group
        ]

        print()
        print("=" * 72)
        print(
            f"Creating LDO fold: {test_group}"
        )
        print("=" * 72)

        print("Training groups:")

        for group in train_groups:
            print(f"  - {group}")

        print("Test group:")
        print(f"  - {test_group}")

        X_train, y_train = load_groups(
            train_groups
        )

        X_test, y_test = load_groups(
            [test_group]
        )

        X_train, y_train = cap_rows(
            X_train,
            y_train,
            max_train_rows,
            random_state,
            "Training cap",
        )

        X_test, y_test = cap_rows(
            X_test,
            y_test,
            max_test_rows,
            random_state,
            "Test cap",
        )

        splits.append(
            (
                test_group,
                X_train,
                y_train,
                X_test,
                y_test,
            )
        )

    return splits


# ---------------------------------------------------------------------------
# Leakage-safe scaling
# ---------------------------------------------------------------------------

def scale_split(X_train, X_test):
    """
    Fit StandardScaler ONLY on X_train.

    Then transform both training and test data using that fitted scaler.
    """

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    ).astype(np.float32)

    X_test_scaled = scaler.transform(
        X_test
    ).astype(np.float32)

    return (
        X_train_scaled,
        X_test_scaled,
        scaler,
    )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calculate_fpr(y_true, y_pred):
    """
    Calculate false-positive rate.

        FPR = FP / (FP + TN)

    Label 0 = benign
    Label 1 = attack
    """

    tn, fp, _, _ = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    ).ravel()

    denominator = fp + tn

    if denominator == 0:
        return 0.0

    return float(
        fp / denominator
    )


def evaluate_predictions(y_true, y_pred):
    """Calculate Accuracy, Macro-F1 and FPR."""

    accuracy = float(
        accuracy_score(
            y_true,
            y_pred,
        )
    )

    macro_f1 = float(
        f1_score(
            y_true,
            y_pred,
            average="macro",
            zero_division=0,
        )
    )

    fpr = calculate_fpr(
        y_true,
        y_pred,
    )

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "fpr": fpr,
    }


# ---------------------------------------------------------------------------
# TensorFlow reproducibility
# ---------------------------------------------------------------------------

def set_tensorflow_seed(random_state):
    """Set TensorFlow/Keras random seed."""

    import tensorflow as tf

    tf.keras.utils.set_random_seed(
        random_state
    )


# ---------------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------------

def train_ensemble(
    X_train,
    y_train,
    X_test,
    random_state,
):
    """Train the soft-voting ensemble."""

    print()
    print("Training Ensemble...")

    model = build_ensemble(
        random_state=random_state
    )

    model.fit(
        X_train,
        y_train,
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities >= 0.5
    ).astype(np.int8)

    return predictions


# ---------------------------------------------------------------------------
# CNN
# ---------------------------------------------------------------------------

def train_cnn(
    X_train,
    y_train,
    X_test,
    random_state,
    epochs,
    batch_size,
):
    """Train the supervised 1D-CNN."""

    print()
    print("Training 1D-CNN...")

    set_tensorflow_seed(
        random_state
    )

    model = build_cnn(
        X_train.shape[1]
    )

    X_train_cnn = X_train.reshape(
        -1,
        X_train.shape[1],
        1,
    )

    X_test_cnn = X_test.reshape(
        -1,
        X_test.shape[1],
        1,
    )

    model.fit(
        X_train_cnn,
        y_train,
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    probabilities = model.predict(
        X_test_cnn,
        verbose=0,
    ).reshape(-1)

    predictions = (
        probabilities >= 0.5
    ).astype(np.int8)

    return predictions


# ---------------------------------------------------------------------------
# Autoencoder
# ---------------------------------------------------------------------------

def train_autoencoder(
    X_train,
    y_train,
    X_test,
    random_state,
    epochs,
    batch_size,
    threshold_percentile,
):
    """
    Train autoencoder ONLY on benign training samples.

    Threshold is derived ONLY from training-benign reconstruction errors.
    Test labels are never used during training or threshold selection.
    """

    print()
    print("Training Autoencoder...")

    set_tensorflow_seed(
        random_state
    )

    benign_train = X_train[
        y_train == 0
    ]

    if benign_train.shape[0] == 0:
        raise ValueError(
            "Autoencoder training set contains "
            "no benign samples."
        )

    print(
        f"  Benign training rows: "
        f"{benign_train.shape[0]:,}"
    )

    model = build_autoencoder(
        X_train.shape[1]
    )

    model.fit(
        benign_train,
        benign_train,
        epochs=epochs,
        batch_size=batch_size,
        verbose=0,
    )

    # Training-benign reconstruction errors.
    train_reconstruction = model.predict(
        benign_train,
        verbose=0,
    )

    train_errors = np.mean(
        np.square(
            benign_train
            - train_reconstruction
        ),
        axis=1,
    )

    threshold = float(
        np.percentile(
            train_errors,
            threshold_percentile,
        )
    )

    print(
        f"  Reconstruction threshold "
        f"({threshold_percentile:g}th percentile): "
        f"{threshold:.8f}"
    )

    # Test reconstruction errors.
    test_reconstruction = model.predict(
        X_test,
        verbose=0,
    )

    test_errors = np.mean(
        np.square(
            X_test
            - test_reconstruction
        ),
        axis=1,
    )

    predictions = (
        test_errors >= threshold
    ).astype(np.int8)

    return predictions


# ---------------------------------------------------------------------------
# Fold execution
# ---------------------------------------------------------------------------

def run_fold(
    model_name,
    dataset_name,
    split_type,
    fold_name,
    X_train,
    y_train,
    X_test,
    y_test,
    random_state,
    epochs,
    batch_size,
    threshold_percentile,
):
    """Scale, train and evaluate one split/fold."""

    print()
    print("=" * 72)
    print(
        f"Running {model_name} | "
        f"{dataset_name} | "
        f"{split_type} | "
        f"fold={fold_name}"
    )
    print("=" * 72)

    print(
        f"Raw training shape: {X_train.shape}"
    )

    print(
        f"Raw test shape: {X_test.shape}"
    )

    # IMPORTANT:
    # Fit the scaler ONLY on training data.
    (
        X_train_scaled,
        X_test_scaled,
        _,
    ) = scale_split(
        X_train,
        X_test,
    )

    print(
        f"Scaled training shape: "
        f"{X_train_scaled.shape}"
    )

    print(
        f"Scaled test shape: "
        f"{X_test_scaled.shape}"
    )

    if model_name == "ensemble":
        y_pred = train_ensemble(
            X_train_scaled,
            y_train,
            X_test_scaled,
            random_state,
        )

    elif model_name == "autoencoder":
        y_pred = train_autoencoder(
            X_train_scaled,
            y_train,
            X_test_scaled,
            random_state,
            epochs,
            batch_size,
            threshold_percentile,
        )

    elif model_name == "cnn":
        y_pred = train_cnn(
            X_train_scaled,
            y_train,
            X_test_scaled,
            random_state,
            epochs,
            batch_size,
        )

    else:
        raise ValueError(
            f"Unsupported model: {model_name}"
        )

    metrics = evaluate_predictions(
        y_test,
        y_pred,
    )

    result = {
        "model": model_name,
        "dataset": dataset_name,
        "split_type": split_type,
        "fold": fold_name,
        "random_state": random_state,
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "train_benign": int(
            np.sum(y_train == 0)
        ),
        "train_attack": int(
            np.sum(y_train == 1)
        ),
        "test_benign": int(
            np.sum(y_test == 0)
        ),
        "test_attack": int(
            np.sum(y_test == 1)
        ),
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "fpr": metrics["fpr"],
    }

    print()
    print(
        f"Accuracy : {result['accuracy']:.6f}"
    )
    print(
        f"Macro-F1 : {result['macro_f1']:.6f}"
    )
    print(
        f"FPR      : {result['fpr']:.6f}"
    )

    return result


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------

RESULT_FIELDS = [
    "model",
    "dataset",
    "split_type",
    "fold",
    "random_state",
    "train_rows",
    "test_rows",
    "train_benign",
    "train_attack",
    "test_benign",
    "test_attack",
    "accuracy",
    "macro_f1",
    "fpr",
]


def write_results(result, output_path):
    """
    Append one result row to a CSV file.

    FIX:
        The function receives one result dictionary named `result`
        and writes that same dictionary.
    """

    output_path = Path(output_path)

    if not output_path.is_absolute():
        output_path = (
            PROJECT_ROOT
            / output_path
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_exists = (
        output_path.exists()
        and output_path.stat().st_size > 0
    )

    with output_path.open(
        "a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=RESULT_FIELDS,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(
            {
                field: result[field]
                for field in RESULT_FIELDS
            }
        )

    print()
    print(
        f"Results written to: {output_path}"
    )


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser():
    """Build command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Milestone 4 IoT botnet "
            "training/evaluation pipeline."
        )
    )

    parser.add_argument(
        "--model",
        required=True,
        choices=[
            "ensemble",
            "autoencoder",
            "cnn",
        ],
        help="Model to train.",
    )

    parser.add_argument(
        "--dataset",
        required=True,
        choices=[
            "nbaiot",
            "medbiot",
        ],
        help="Dataset to use.",
    )

    parser.add_argument(
        "--split",
        required=True,
        choices=[
            "random",
            "ldo",
        ],
        help="Evaluation split protocol.",
    )

    parser.add_argument(
        "--fold",
        default=None,
        help=(
            "Specific LDO fold/group. "
            "Only valid with --split ldo."
        ),
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Random split test fraction.",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Random seed.",
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=DEFAULT_EPOCHS,
        help="Neural-network training epochs.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Neural-network batch size.",
    )

    parser.add_argument(
        "--autoencoder-threshold-percentile",
        type=float,
        default=DEFAULT_AUTOENCODER_THRESHOLD_PERCENTILE,
        help=(
            "Training-benign reconstruction error "
            "percentile for the anomaly threshold."
        ),
    )

    parser.add_argument(
        "--max-train-rows",
        type=int,
        default=None,
        help=(
            "Optional stratified training-row cap "
            "for smoke tests."
        ),
    )

    parser.add_argument(
        "--max-test-rows",
        type=int,
        default=None,
        help=(
            "Optional stratified test-row cap "
            "for smoke tests."
        ),
    )

    parser.add_argument(
        "--output",
        default="results/raw_metrics.csv",
        help="CSV file for metric logging.",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args()

    # Basic validation.
    if not (
        0.0 < args.test_size < 1.0
    ):
        raise ValueError(
            "--test-size must be between 0 and 1."
        )

    if args.epochs <= 0:
        raise ValueError(
            "--epochs must be greater than 0."
        )

    if args.batch_size <= 0:
        raise ValueError(
            "--batch-size must be greater than 0."
        )

    if not (
        0.0
        < args.autoencoder_threshold_percentile
        < 100.0
    ):
        raise ValueError(
            "--autoencoder-threshold-percentile "
            "must be between 0 and 100."
        )

    if (
        args.max_train_rows is not None
        and args.max_train_rows <= 0
    ):
        raise ValueError(
            "--max-train-rows must be greater than 0."
        )

    if (
        args.max_test_rows is not None
        and args.max_test_rows <= 0
    ):
        raise ValueError(
            "--max-test-rows must be greater than 0."
        )

    if not PROCESSED_DIR.exists():
        raise FileNotFoundError(
            f"Milestone 4 data directory not found: "
            f"{PROCESSED_DIR}\n"
            f"Run the preprocessing pipeline first."
        )

    if args.dataset == "nbaiot":
        group_names = NBAIOT_GROUPS
    else:
        group_names = MEDBIOT_GROUPS

    print("=" * 72)
    print(
        "Milestone 4 - IoT Botnet "
        "Training/Evaluation"
    )
    print("=" * 72)

    print(
        f"Model       : {args.model}"
    )

    print(
        f"Dataset     : {args.dataset}"
    )

    print(
        f"Split       : {args.split}"
    )

    print(
        f"Data source : {PROCESSED_DIR}"
    )

    # -----------------------------------------------------------------------
    # Random split
    # -----------------------------------------------------------------------

    if args.split == "random":

        if args.fold is not None:
            raise ValueError(
                "--fold is only valid with --split ldo."
            )

        (
            X_train,
            y_train,
            X_test,
            y_test,
        ) = make_random_split(
            group_names,
            args.test_size,
            args.random_state,
            args.max_train_rows,
            args.max_test_rows,
        )

        result = run_fold(
            model_name=args.model,
            dataset_name=args.dataset,
            split_type="random",
            fold_name="random_split",
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            random_state=args.random_state,
            epochs=args.epochs,
            batch_size=args.batch_size,
            threshold_percentile=(
                args.autoencoder_threshold_percentile
            ),
        )

        write_results(
            result,
            args.output,
        )

        return

    # -----------------------------------------------------------------------
    # LDO
    # -----------------------------------------------------------------------

    splits = make_ldo_splits(
        group_names,
        fold=args.fold,
        max_train_rows=args.max_train_rows,
        max_test_rows=args.max_test_rows,
        random_state=args.random_state,
    )

    for (
        fold_name,
        X_train,
        y_train,
        X_test,
        y_test,
    ) in splits:

        result = run_fold(
            model_name=args.model,
            dataset_name=args.dataset,
            split_type="ldo",
            fold_name=fold_name,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            random_state=args.random_state,
            epochs=args.epochs,
            batch_size=args.batch_size,
            threshold_percentile=(
                args.autoencoder_threshold_percentile
            ),
        )

        write_results(
            result,
            args.output,
        )


if __name__ == "__main__":
    main()