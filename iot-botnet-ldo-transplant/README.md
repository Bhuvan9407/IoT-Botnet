# IoT Botnet Detection: Leave-Device-Out Evaluation

**Research title:** Established IoT Botnet Detectors Under Leave-Device-Out Evaluation: A Transplant Comparison on N-BaIoT and the Under-Cited MedBIoT Dataset

## Overview
This project investigates established IoT botnet detection approaches under random train/test splits and Leave-Device-Out (LDO) evaluation using N-BaIoT and MedBIoT.

Planned detector families:
- Ensemble models
- Autoencoders
- 1D convolutional neural networks (1D-CNNs)

The experiments will examine whether model performance and relative behavior change across evaluation protocols and datasets. Results are not assumed in advance.

## Repository status
This is a research scaffold containing documentation and directory structure. Experiment code, validated feature mappings, and results should be added as they are completed.

## Structure
```text
.
├── data/
│   ├── raw/          # Original datasets (excluded from Git)
│   └── processed/    # Derived datasets (excluded from Git)
├── docs/
│   └── milestone-1/  # Literature review and schema investigation
├── models/           # Saved model artifacts (excluded from Git)
├── notebooks/        # Exploration and experiment notebooks
├── results/          # Metrics, tables, and figures
├── src/              # Reusable preprocessing/training/evaluation code
└── tests/            # Data and evaluation tests
```

## Datasets
Dataset files are not included. Obtain them from their original sources and place them under `data/raw/`. Check license and usage terms before redistribution.

The initial feature-schema investigation is in `docs/milestone-1/feature-schema-investigation.md`. Similar column names are not treated as proof of semantic equivalence. Validate any cross-dataset mapping before using it.

## Reproducibility
As experiments are implemented, record dataset provenance, preprocessing and label construction, device-level splits, random seeds, model configurations, metrics, software versions, and hardware.

## Milestone 1 status
- Four-paper literature review drafted.
- Initial feature-schema investigation documented.
- Basic Keras 1D-CNN construction and forward-pass check completed.

Further validation and experiment implementation remain in progress.
