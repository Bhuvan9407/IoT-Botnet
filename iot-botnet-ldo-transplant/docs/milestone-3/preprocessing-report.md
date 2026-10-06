# Milestone 3 — Data Preprocessing Report

## 1. Objective

Milestone 3 transforms the staged N-BaIoT and MedBIoT raw CSV files into a common standardized representation suitable for subsequent Leave-Device-Out (LDO) evaluation.

The preprocessing pipeline operates on the 107 staged raw files listed in `data/raw/manifest.txt`: 89 N-BaIoT files and 18 MedBIoT files. The resulting representation contains 100 input features and one binary label column.

The preprocessing is implemented in `src/data/prep.py`, with generated outputs stored under `data/processed/`.

## 2. Feature Standardization — 100-Feature Rule

N-BaIoT contains 115 features, while MedBIoT contains 100 features. The additional 15 N-BaIoT features belong to the `H` (Host) feature family.

Therefore, the mandated 100-feature representation is obtained by:

- removing all 15 `H_*` features from N-BaIoT;
- retaining the remaining 100 N-BaIoT features;
- retaining all 100 MedBIoT features.

The resulting common feature structure consists of:

### MI_dir — 15 features

For windows `5`, `3`, `1`, `0.1`, and `0.01`:

```text
MI_dir_<window>_weight
MI_dir_<window>_mean
MI_dir_<window>_std
```

### HH — 35 features

For each of the five windows:

```text
HH_<window>_weight
HH_<window>_mean
HH_<window>_std
HH_<window>_magnitude
HH_<window>_radius
HH_<window>_covariance
HH_<window>_pcc
```

### HH_jit — 15 features

For each of the five windows:

```text
HH_jit_<window>_weight
HH_jit_<window>_mean
HH_jit_<window>_std
```

### HpHp — 35 features

For each of the five windows:

```text
HpHp_<window>_weight
HpHp_<window>_mean
HpHp_<window>_std
HpHp_<window>_magnitude
HpHp_<window>_radius
HpHp_<window>_covariance
HpHp_<window>_pcc
```

This gives exactly:

```text
15 + 35 + 15 + 35 = 100 features
```

The source schemas use different naming conventions. In particular, N-BaIoT uses `L`-prefixed window names such as `L5`, while MedBIoT uses names such as `5`. N-BaIoT also uses `variance` for some statistics where MedBIoT uses `std`. The preprocessing establishes a canonical positional feature representation for the comparison, but this naming normalization does **not** claim that variance and standard deviation are mathematically identical. The original source values are retained rather than being silently treated as equivalent statistics.

## 3. Binary Label Construction

Labels are generated directly from the raw filenames because the inspected raw CSV files do not contain a separate label column.

The binary convention is:

```text
0 = benign / legitimate traffic
1 = attack / malicious traffic
```

For N-BaIoT, `benign_traffic.csv` is assigned label `0`; every other attack file is assigned label `1`.

For MedBIoT, files containing `_leg_` or `_legit_` are assigned label `0`; all remaining files are assigned label `1`.

No synthetic labels were introduced.

## 4. Stratified Subsampling

To reduce volume-driven bias during later LDO experiments, subsampling is performed independently within each class for each LDO grouping unit.

The maximum retained number is:

```text
100,000 benign rows per device/device-type
100,000 attack rows per device/device-type
```

When a class contains fewer than 100,000 rows, all available rows are retained. No oversampling or duplication is performed.

A fixed random seed of `42` is used whenever sampling is required, making the preprocessing reproducible.

For LDO grouping:

- each physical N-BaIoT device is treated as one grouping unit;
- MedBIoT is grouped by device type (`fan`, `light`, and `switch`).

This produces 12 processed grouping units in total.

## 5. Scaling

`StandardScaler` is applied after class-wise subsampling and final row shuffling.

For Milestone 3, the scaler is fitted independently for each processed device/device-type grouping. This provides a standardized staging representation without mixing the scaling statistics of different LDO units.

These saved scaled arrays are intended as Milestone 3 preprocessing artifacts. They must **not** be treated as the final leakage-free preprocessing for LDO evaluation. In the final experiments, the scaler must be fitted using training devices/folds only and then applied to the held-out device.

## 6. Final Processed Dataset Sizes

The preprocessing generated 12 `.npy` files, each containing 100 features plus one label column.

| Dataset | LDO unit | Benign rows | Attack rows | Total rows | Shape |
|---|---|---:|---:|---:|---|
| MedBIoT | fan | 100,000 | 100,000 | 200,000 | `(200000, 101)` |
| MedBIoT | light | 100,000 | 100,000 | 200,000 | `(200000, 101)` |
| MedBIoT | switch | 100,000 | 100,000 | 200,000 | `(200000, 101)` |
| N-BaIoT | Danmini_Doorbell | 49,548 | 100,000 | 149,548 | `(149548, 101)` |
| N-BaIoT | Ecobee_Thermostat | 13,113 | 100,000 | 113,113 | `(113113, 101)` |
| N-BaIoT | Ennio_Doorbell | 39,100 | 100,000 | 139,100 | `(139100, 101)` |
| N-BaIoT | Philips_B120N10_Baby_Monitor | 100,000 | 100,000 | 200,000 | `(200000, 101)` |
| N-BaIoT | Provision_PT_737E_Security_Camera | 62,154 | 100,000 | 162,154 | `(162154, 101)` |
| N-BaIoT | Provision_PT_838_Security_Camera | 98,514 | 100,000 | 198,514 | `(198514, 101)` |
| N-BaIoT | Samsung_SNH_1011_N_Webcam | 52,150 | 100,000 | 152,150 | `(152150, 101)` |
| N-BaIoT | SimpleHome_XCS7_1002_WHT_Security_Camera | 46,585 | 100,000 | 146,585 | `(146585, 101)` |
| N-BaIoT | SimpleHome_XCS7_1003_WHT_Security_Camera | 19,528 | 100,000 | 119,528 | `(119528, 101)` |

The unequal totals for several N-BaIoT devices arise because their available benign traffic is below the 100,000-row cap. The attack class is capped at 100,000 rows where sufficient data exists.

## 7. Output Artifacts

The preprocessing pipeline generated:

```text
data/processed/fan_processed.npy
data/processed/light_processed.npy
data/processed/switch_processed.npy
data/processed/Danmini_Doorbell_processed.npy
data/processed/Ecobee_Thermostat_processed.npy
data/processed/Ennio_Doorbell_processed.npy
data/processed/Philips_B120N10_Baby_Monitor_processed.npy
data/processed/Provision_PT_737E_Security_Camera_processed.npy
data/processed/Provision_PT_838_Security_Camera_processed.npy
data/processed/Samsung_SNH_1011_N_Webcam_processed.npy
data/processed/SimpleHome_XCS7_1002_WHT_Security_Camera_processed.npy
data/processed/SimpleHome_XCS7_1003_WHT_Security_Camera_processed.npy
data/processed/summary_log.csv
```

`summary_log.csv` records the processed file, dataset, LDO unit, row count, feature count, and class counts.

The raw and generated processed datasets remain excluded from normal Git tracking through the repository `.gitignore`. The preprocessing code, report, and summary metadata are the reproducible project artifacts.

## 8. Validation

The completed preprocessing run successfully processed all 107 manifest entries into 12 LDO grouping units.

A final integrity check confirmed:

- 12 processed `.npy` files were generated;
- every processed array has exactly 101 columns;
- all feature/label values are finite;
- labels contain only `0` and `1`.

Therefore, the Milestone 3 preprocessing pipeline completed successfully and produced the required standardized dataset artifacts for the next stage of the project.

## 9. Reproducibility

The complete preprocessing operation can be reproduced from the repository root with:

```powershell
python .\src\data\prep.py
```

The pipeline reads its input file list from:

```text
data/raw/manifest.txt
```

and uses a fixed random seed (`42`) for deterministic class-wise subsampling and output shuffling.
