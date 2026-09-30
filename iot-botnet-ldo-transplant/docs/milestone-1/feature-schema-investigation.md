# Feature-schema investigation

## Purpose
This note records the initial comparison of the N-BaIoT and MedBIoT feature schemas. It is an investigation record, not proof that similarly named features are semantically identical.

## Observations
- The inspected MedBIoT CSV header contains 100 feature columns and no separate label column.
- The inspected N-BaIoT schema contains 115 feature columns.
- Both inspected schemas include `MI_dir`, `HH`, `HH_jit`, and `HpHp` families.
- N-BaIoT also includes an `H` family that was not present in the inspected MedBIoT schema.
- Naming differs, including window notation (`5` versus `L5`) and statistical terminology (`std` versus `variance`).

## Feature families noted

### MedBIoT
The inspected schema contains `MI_dir` statistics over windows `5`, `3`, `1`, `0.1`, and `0.01`, plus `HH`, `HH_jit`, and `HpHp` statistics over five windows. The inspected `HH` and `HpHp` families include weight, mean, standard deviation, radius, magnitude, covariance, and PCC fields.

### N-BaIoT
The inspected schema contains `MI_dir_L`, `H_L`, `HH_L`, `HH_jit_L`, and `HpHp_L` families over five windows. The inspected `MI_dir`, `H`, and `HH_jit` fields use variance terminology, while `HH` and `HpHp` include mean, standard deviation, magnitude, radius, covariance, and PCC fields.

## Implementation reference examined
The Kitsune `AfterImage.py` / `.pyx` implementation was inspected as a code-level reference for incremental statistics, including mean, variance, standard deviation, radius, magnitude, covariance, and PCC.

This reference helps interpret statistic names, but does not establish that the N-BaIoT and MedBIoT generation pipelines use identical formulas, preprocessing, or feature ordering.

## Current conclusion
The schemas are not directly interchangeable based on column names alone. N-BaIoT has an additional `H` family, and window/statistic naming differs. Semantic equivalence and exact preprocessing still need validation.

For now, use each dataset's native schema for within-dataset experiments. Define a cross-dataset common feature set only after validating feature meaning and construction. Do not silently pad missing features or assume similarly named columns are equivalent.

## Evidence and scope
These observations reflect the headers and code references inspected during the initial investigation. Zero missing values were observed in the first 10,000 rows only; this is not a full-file missingness check.

## Remaining checks
- Verify the full MedBIoT file's row count, data types, missing values, and label construction.
- Confirm the precise feature definitions and preprocessing used by each dataset.
- Document the exact feature mapping if cross-dataset comparison requires one.
