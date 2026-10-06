"""
Milestone 3 preprocessing pipeline.

Transforms the staged N-BaIoT and MedBIoT CSV files into a common
100-feature binary classification format.

Outputs:
    data/processed/<device>_processed.npy
    data/processed/summary_log.csv

    data/processed_unscaled/<device>_unscaled.npy

Each .npy file contains:
    100 canonical features + 1 binary label column

The files in data/processed are the original Milestone 3 staging outputs
with per-device StandardScaler normalization.

The files in data/processed_unscaled contain the same canonical features
without per-device scaling. Milestone 4 uses these unscaled files so that
its scaler can be fitted only on the training split/fold.

Important:
    The StandardScaler used here is staging-only.
    Final Leave-Device-Out experiments must fit preprocessing/scaling on
    training devices only.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "manifest.txt"

# Original Milestone 3 output.
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

# Leakage-safe source data for Milestone 4.
UNSCALED_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed_unscaled"

RANDOM_SEED = 42
MAX_ROWS_PER_CLASS = 100_000


# ---------------------------------------------------------------------------
# Canonical 100-feature schema
# ---------------------------------------------------------------------------

WINDOWS = ["5", "3", "1", "0.1", "0.01"]

CANONICAL_FEATURES = []

# MI_dir: 5 windows × 3 statistics = 15
for window in WINDOWS:
    CANONICAL_FEATURES.extend(
        [
            f"MI_dir_{window}_weight",
            f"MI_dir_{window}_mean",
            f"MI_dir_{window}_std",
        ]
    )

# HH: 5 windows × 7 statistics = 35
for window in WINDOWS:
    CANONICAL_FEATURES.extend(
        [
            f"HH_{window}_weight",
            f"HH_{window}_mean",
            f"HH_{window}_std",
            f"HH_{window}_magnitude",
            f"HH_{window}_radius",
            f"HH_{window}_covariance",
            f"HH_{window}_pcc",
        ]
    )

# HH_jit: 5 windows × 3 statistics = 15
for window in WINDOWS:
    CANONICAL_FEATURES.extend(
        [
            f"HH_jit_{window}_weight",
            f"HH_jit_{window}_mean",
            f"HH_jit_{window}_std",
        ]
    )

# HpHp: 5 windows × 7 statistics = 35
for window in WINDOWS:
    CANONICAL_FEATURES.extend(
        [
            f"HpHp_{window}_weight",
            f"HpHp_{window}_mean",
            f"HpHp_{window}_std",
            f"HpHp_{window}_magnitude",
            f"HpHp_{window}_radius",
            f"HpHp_{window}_covariance",
            f"HpHp_{window}_pcc",
        ]
    )


if len(CANONICAL_FEATURES) != 100:
    raise RuntimeError(
        f"Expected exactly 100 canonical features, "
        f"got {len(CANONICAL_FEATURES)}."
    )


# ---------------------------------------------------------------------------
# Feature-name mapping
# ---------------------------------------------------------------------------

def normalize_feature_name(column: str) -> str:
    """
    Convert an N-BaIoT or MedBIoT feature name into the canonical name.

    Examples:
        N-BaIoT:
            MI_dir_L5_variance -> MI_dir_5_std
            HH_L5_std          -> HH_5_std

        MedBIoT:
            MI_dir_5_std       -> MI_dir_5_std
            HH_5_radius_0_1    -> HH_5_radius
    """

    name = column.strip()

    # Remove N-BaIoT window prefix L.
    name = re.sub(
        r"_L(5|3|1|0\.1|0\.01)_",
        r"_\1_",
        name
    )

    # Handle the end of a feature name if necessary.
    name = re.sub(
        r"_L(5|3|1|0\.1|0\.01)$",
        r"_\1",
        name
    )

    # MedBIoT suffixes such as _0 and _0_1.
    name = re.sub(
        r"_(0|0_1)$",
        "",
        name
    )

    # Dataset terminology difference:
    # N-BaIoT uses variance where the corresponding MedBIoT
    # field uses std.
    if name.endswith("_variance"):
        name = (
            name[: -len("_variance")]
            + "_std"
        )

    return name


def build_feature_mapping(columns):
    """
    Build canonical feature -> source column mapping.

    Raises an error if:
      - a required canonical feature is missing
      - multiple source columns map to the same canonical feature
    """

    mapping = {}

    for column in columns:
        canonical = normalize_feature_name(column)

        # N-BaIoT H_* fields are deliberately excluded.
        if canonical.startswith("H_"):
            continue

        if canonical in mapping:
            raise ValueError(
                f"Multiple source columns map to canonical feature "
                f"'{canonical}': '{mapping[canonical]}' and '{column}'"
            )

        mapping[canonical] = column

    missing = [
        feature
        for feature in CANONICAL_FEATURES
        if feature not in mapping
    ]

    if missing:
        raise ValueError(
            "Required canonical features are missing:\n"
            + "\n".join(missing)
        )

    return {
        feature: mapping[feature]
        for feature in CANONICAL_FEATURES
    }


# ---------------------------------------------------------------------------
# Manifest handling
# ---------------------------------------------------------------------------

def read_manifest():
    """Read the raw-data manifest using UTF-8-SIG to handle its BOM."""

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_PATH}"
        )

    with MANIFEST_PATH.open(
        "r",
        encoding="utf-8-sig"
    ) as file:
        entries = [
            line.strip()
            for line in file
            if line.strip()
            and not line.strip().startswith("#")
        ]

    if not entries:
        raise ValueError("Manifest is empty.")

    return entries


# ---------------------------------------------------------------------------
# Dataset/device identification
# ---------------------------------------------------------------------------

def identify_source(relative_path):
    """
    Identify whether a manifest entry belongs to N-BaIoT or MedBIoT.
    """

    normalized = relative_path.replace("\\", "/")

    if normalized.startswith("data/raw/nbaiot/"):
        return "N-BaIoT"

    if normalized.startswith("data/raw/medbiot/"):
        return "MedBIoT"

    raise ValueError(
        f"Unknown dataset path in manifest: {relative_path}"
    )


def identify_group(relative_path, dataset):
    """
    Return the LDO grouping unit.

    N-BaIoT:
        physical device directory

    MedBIoT:
        device type: fan / light / switch
    """

    normalized = relative_path.replace("\\", "/")
    parts = normalized.split("/")

    if dataset == "N-BaIoT":
        # data/raw/nbaiot/extracted/<Device>/<file>.csv
        try:
            extracted_index = parts.index("extracted")
            return parts[extracted_index + 1]
        except (ValueError, IndexError):
            raise ValueError(
                f"Could not determine N-BaIoT device from: "
                f"{relative_path}"
            )

    # data/raw/medbiot/<filename>.csv
    filename = Path(parts[-1]).stem.lower()

    for device_type in (
        "fan",
        "light",
        "switch",
    ):
        if device_type in filename:
            return device_type

    raise ValueError(
        f"Could not determine MedBIoT device type from: "
        f"{relative_path}"
    )


# ---------------------------------------------------------------------------
# Label identification
# ---------------------------------------------------------------------------

def identify_label(relative_path):
    """
    Assign binary labels based on the filename.

    0 = benign / legitimate
    1 = attack / malicious
    """

    filename = Path(relative_path).name.lower()

    # N-BaIoT benign file.
    if filename == "benign_traffic.csv":
        return 0

    # MedBIoT legitimate files.
    if "_leg_" in filename or "_legit_" in filename:
        return 0

    # Everything else is treated as attack/malicious.
    return 1


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csv(relative_path):
    """Load one raw CSV file."""

    path = PROJECT_ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(
            f"Manifest file does not exist: {path}"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(
            f"CSV is empty: {path}"
        )

    return df


# ---------------------------------------------------------------------------
# Per-device processing
# ---------------------------------------------------------------------------

def process_group(dataset, group_name, files):
    """
    Combine all raw CSVs belonging to one LDO grouping unit.
    """

    print()
    print("=" * 72)
    print(
        f"Processing: {dataset} / {group_name}"
    )
    print("=" * 72)

    class_frames = {
        0: [],
        1: [],
    }

    feature_mapping = None

    for relative_path in files:
        label = identify_label(relative_path)

        print(
            f"  Reading: {Path(relative_path).name}"
            f" -> label={label}"
        )

        df = load_csv(relative_path)

        # Establish and validate the source schema.
        current_mapping = build_feature_mapping(
            df.columns
        )

        if feature_mapping is None:
            feature_mapping = current_mapping
        elif feature_mapping != current_mapping:
            raise ValueError(
                f"Feature mapping differs between files in "
                f"{dataset}/{group_name}: {relative_path}"
            )

        # Select the canonical 100 features in exact order.
        X = df[
            [
                feature_mapping[feature]
                for feature in CANONICAL_FEATURES
            ]
        ].copy()

        # Force numeric representation.
        X = X.apply(
            pd.to_numeric,
            errors="coerce"
        )

        if X.isna().any().any():
            bad_columns = (
                X.columns[
                    X.isna().any()
                ].tolist()
            )

            raise ValueError(
                f"Non-numeric or missing values detected in "
                f"{relative_path}. "
                f"Affected canonical columns: "
                f"{bad_columns}"
            )

        class_frames[label].append(X)

    # -----------------------------------------------------------------------
    # Combine each class separately so sampling is class-balanced.
    # -----------------------------------------------------------------------

    class_arrays = {}

    for label in (0, 1):
        if not class_frames[label]:
            raise ValueError(
                f"No rows found for class {label} in "
                f"{dataset}/{group_name}"
            )

        class_df = pd.concat(
            class_frames[label],
            ignore_index=True
        )

        original_rows = len(class_df)

        # Fixed random-state class-wise cap.
        if original_rows > MAX_ROWS_PER_CLASS:
            class_df = class_df.sample(
                n=MAX_ROWS_PER_CLASS,
                random_state=RANDOM_SEED
            ).reset_index(drop=True)

        print(
            f"  Class {label}: "
            f"{original_rows:,} -> "
            f"{len(class_df):,} rows"
        )

        class_arrays[label] = (
            class_df.to_numpy(
                dtype=np.float64
            )
        )

    # -----------------------------------------------------------------------
    # Combine the two classes.
    # -----------------------------------------------------------------------

    X = np.vstack(
        [
            class_arrays[0],
            class_arrays[1],
        ]
    )

    y = np.concatenate(
        [
            np.zeros(
                len(class_arrays[0]),
                dtype=np.int8
            ),
            np.ones(
                len(class_arrays[1]),
                dtype=np.int8
            ),
        ]
    )

    # -----------------------------------------------------------------------
    # Shuffle the final dataset so classes are not stored in blocks.
    # -----------------------------------------------------------------------

    rng = np.random.default_rng(
        RANDOM_SEED
    )

    permutation = rng.permutation(
        len(y)
    )

    X = X[permutation]
    y = y[permutation]

    # -----------------------------------------------------------------------
    # Milestone 4 leakage-safe source data
    # -----------------------------------------------------------------------
    #
    # Save the canonical features WITHOUT per-device scaling.
    #
    # Milestone 4 will fit StandardScaler only on the training data
    # for each random split or LDO fold.
    # -----------------------------------------------------------------------

    unscaled_output = np.column_stack(
        [
            X.astype(np.float32),
            y,
        ]
    )

    unscaled_output_filename = (
        f"{group_name}_unscaled.npy"
    )

    unscaled_output_path = (
        UNSCALED_OUTPUT_DIR
        / unscaled_output_filename
    )

    np.save(
        unscaled_output_path,
        unscaled_output
    )

    # -----------------------------------------------------------------------
    # Milestone 3 staging scaler
    # -----------------------------------------------------------------------
    #
    # This preserves the original Milestone 3 output.
    # It must NOT be used for the final leakage-sensitive LDO experiments.
    # -----------------------------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # Label becomes the final 101st column.
    output = np.column_stack(
        [
            X_scaled.astype(np.float32),
            y,
        ]
    )

    output_filename = (
        f"{group_name}_processed.npy"
    )

    output_path = (
        OUTPUT_DIR
        / output_filename
    )

    np.save(
        output_path,
        output
    )

    class_0_count = int(
        np.sum(y == 0)
    )

    class_1_count = int(
        np.sum(y == 1)
    )

    print(
        f"  Saved staged:    {output_path}"
    )

    print(
        f"  Saved unscaled:  {unscaled_output_path}"
    )

    print(
        f"  Shape: {output.shape}"
    )

    print(
        f"  Class balance: "
        f"0={class_0_count:,}, "
        f"1={class_1_count:,}"
    )

    return {
        "dataset": dataset,
        "group": group_name,
        "output_file": output_filename,
        "rows": int(output.shape[0]),
        "columns": int(output.shape[1]),
        "features": 100,
        "benign_rows": class_0_count,
        "attack_rows": class_1_count,
        "class_balance": (
            f"0={class_0_count},"
            f"1={class_1_count}"
        ),
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print(
        "Milestone 3 - IoT Botnet Data Preprocessing"
    )
    print("=" * 72)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    UNSCALED_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    manifest_entries = read_manifest()

    print(
        f"Manifest entries: "
        f"{len(manifest_entries)}"
    )

    # -----------------------------------------------------------------------
    # Group manifest entries
    # -----------------------------------------------------------------------

    groups = {}

    for relative_path in manifest_entries:
        dataset = identify_source(
            relative_path
        )

        group_name = identify_group(
            relative_path,
            dataset
        )

        key = (
            dataset,
            group_name
        )

        groups.setdefault(
            key,
            []
        ).append(relative_path)

    print(
        f"Processing groups: "
        f"{len(groups)}"
    )

    # -----------------------------------------------------------------------
    # Process every device/device-type
    # -----------------------------------------------------------------------

    summary_rows = []

    for (
        dataset,
        group_name
    ), files in sorted(groups.items()):

        result = process_group(
            dataset,
            group_name,
            files
        )

        summary_rows.append(result)

    # -----------------------------------------------------------------------
    # Summary log
    # -----------------------------------------------------------------------

    summary_df = pd.DataFrame(
        summary_rows
    )

    summary_path = (
        OUTPUT_DIR
        / "summary_log.csv"
    )

    summary_df.to_csv(
        summary_path,
        index=False
    )

    print()
    print("=" * 72)
    print(
        "Milestone 3 preprocessing complete."
    )
    print("=" * 72)

    print(
        f"Processed groups : "
        f"{len(summary_df)}"
    )

    print(
        f"Summary log      : "
        f"{summary_path}"
    )

    print(
        f"Unscaled data    : "
        f"{UNSCALED_OUTPUT_DIR}"
    )

    print()

    print(
        summary_df.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()