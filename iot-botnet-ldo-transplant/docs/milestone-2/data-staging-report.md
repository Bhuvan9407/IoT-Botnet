# Milestone 2: Dataset Collection and Staging Report

## 1. Objective

The objective of Milestone 2 was to collect and stage the N-BaIoT and MedBIoT datasets for the IoT botnet detection research project.

The original requirement specified 99 N-BaIoT CSV files and 18 selected MedBIoT CSV files. Following verification of the available data and approval to proceed, the project uses 89 N-BaIoT device-specific CSV files and 18 MedBIoT CSV files, for a total of 107 files.

## 2. N-BaIoT Dataset

### Source

The specified Hugging Face repository was:

https://huggingface.co/datasets/codymlewis/nbaiot

Inspection using the Hugging Face API showed that the repository contains `.gitattributes`, `README.md`, and `nbaiot.py`, rather than the expected 99 CSV files.

The original UCI dataset was therefore downloaded from:

https://archive.ics.uci.edu/static/public/442/detection+of+iot+botnet+attacks+n+baiot.zip

### Download and extraction procedure

1. Downloaded the original UCI N-BaIoT ZIP archive using `curl`.
2. Verified the integrity of the downloaded archive.
3. Extracted the archive using 7-Zip.
4. Extracted the Gafgyt and Mirai RAR archives for each device.
5. Organized attack files into separate `gafgyt` and `mirai` directories to prevent files with identical names from overwriting one another.
6. Recursively inspected the extracted CSV files and counted the device-specific files.

### Available files

| Category                        | Number of CSV files |
| ------------------------------- | ------------------: |
| Benign traffic                  |                   9 |
| Gafgyt attacks                  |                  45 |
| Mirai attacks                   |                  35 |
| **Total device-specific files** |              **89** |

The original archive contains nine device folders. The Ennio Doorbell and Samsung SNH 1011 N Webcam folders do not contain Mirai attack archives. Consequently, the extracted dataset provides 89 device-specific CSV files rather than the expected 99.

The archive also contains `demonstrate_structure.csv`. This file is not included in the device-specific dataset count.

### Dataset discrepancy

The original UCI archive yielded 89 device-specific CSV files. The expected count of 99 could not be verified from the specified Hugging Face repository or the downloaded UCI archive.

No files were duplicated or fabricated to meet the original count. The decision to proceed with the available 89 N-BaIoT files was approved by the project guide.

## 3. MedBIoT Dataset

### Source

Kaggle dataset:

https://www.kaggle.com/datasets/shaily20/medbiot-legit-and-malware

### Collection procedure

The 18 required CSV files were downloaded and staged in `data/raw/medbiot`.

The selected files cover three device types: fan, light, and switch. The lock device was excluded, as specified in the project instructions.

The selected files include legitimate traffic and Bashlite and Mirai malware traffic, covering C&C and spread stages.

### File count

| Category           | Number of CSV files |
| ------------------ | ------------------: |
| Legitimate traffic |                   6 |
| Malware traffic    |                  12 |
| **Total**          |              **18** |

All 18 selected files were downloaded successfully.

## 4. Final Dataset Status

| Dataset   | Expected | Available |
| --------- | -------: | --------: |
| N-BaIoT   |       99 |        89 |
| MedBIoT   |       18 |        18 |
| **Total** |  **117** |   **107** |

The final staged collection contains 107 dataset CSV files. The N-BaIoT discrepancy is documented, and the project guide approved proceeding with the available files.

## 5. Data Organization and Integrity

The original dataset files are retained in their organized directory structure under `data/raw/`. N-BaIoT attack files are separated by device and attack family to preserve their identity and avoid filename collisions.

Raw dataset files are excluded from GitHub using the repository's `.gitignore` configuration. Only documentation, scripts, and a file manifest should be committed.
