# Milestone 5 — Random-Split Baseline Report



## 1. Objective



Milestone 5 establishes the random-split baseline for the three planned IoT botnet detection model arms:



1. **Ensemble classifier**

   - Random Forest

   - Extra Trees

   - Gradient Boosting



2. **Autoencoder**

   - Unsupervised anomaly detection

   - Trained only using benign training samples



3. **1D Convolutional Neural Network**

   - Supervised binary classification



The objective is to establish a reproducible row-level random-split baseline on both N-BaIoT and MedBIoT before performing the Leave-Device-Out (LDO) evaluation.



The baseline consists of:



- 2 datasets

- 3 model arms

- 3 random seeds



for a total of **18 experiments**.



---



## 2. Experimental Configuration



All experiments use the unified Milestone 4 training and evaluation infrastructure.



### Datasets



- N-BaIoT

- MedBIoT



The leakage-safe unscaled canonical feature arrays are loaded from:



`data/processed_unscaled/`



Each sample contains:



- 100 canonical feature columns

- 1 binary label column



Labels are:



- `0` = benign / legitimate

- `1` = attack / malicious



### Random Split



The random protocol performs a stratified row-level train/test split within the selected dataset.



Configuration used for all 18 experiments:



- Test fraction: `20%`

- Stratification: enabled

- Training cap: `160,000` rows

- Test cap: `40,000` rows

- Random seeds: `42`, `43`, `44`



The same row limits were applied across all model arms and both datasets to maintain a consistent experimental budget.



---



## 3. Leakage-Safe Scaling



The experiments use the unscaled Milestone 3 arrays stored under:



`data/processed_unscaled/`



For every random split:



1. The dataset is divided into training and test partitions.

2. `StandardScaler` is fitted using the training partition only.

3. The fitted scaler transforms the training partition.

4. The same fitted scaler transforms the test partition.



Therefore, test samples do not contribute to the calculation of the scaling parameters.



This preserves the leakage-safe preprocessing procedure established in Milestone 4.



---



## 4. Model Configuration



### 4.1 Ensemble



The ensemble is a soft-voting classifier consisting of:



- Random Forest

- Extra Trees

- Gradient Boosting



The ensemble uses the supplied random seed for reproducibility.



### 4.2 Autoencoder



The autoencoder is trained only on benign training samples.



For each experiment:



1. The training split is created.

2. Samples with `label = 0` are selected.

3. The autoencoder is trained on those benign samples.

4. Reconstruction error is calculated on the benign training samples.

5. The anomaly threshold is selected using the 95th percentile of the training-benign reconstruction-error distribution.

6. The complete test set is evaluated.

7. Samples whose reconstruction error is greater than or equal to the threshold are classified as attacks.



The test labels are not used to determine the threshold.



### 4.3 1D-CNN



The CNN is a supervised binary classifier.



The 100-dimensional feature vector is reshaped to:



`(100, 1)`



The prototype consists of:



- 1D convolution

- max pooling

- flattening

- dense hidden layer

- sigmoid binary-output layer



The random-split experiments use:



- 5 epochs

- batch size: 256



---



## 5. Evaluation Metrics



All three model arms use the same metrics.



### Accuracy



Overall fraction of correctly classified samples.



### Macro-F1



F1 score is calculated independently for the benign and attack classes and then averaged.



Macro-F1 gives equal importance to both classes.



### False Positive Rate



FPR is defined as:



`FPR = FP / (FP + TN)`



where:



- `TN` = benign samples correctly identified as benign

- `FP` = benign samples incorrectly classified as attacks



The project uses:



- class `0` = benign

- class `1` = attack



---



## 6. Experiment Coverage



The complete experiment matrix contains:



| Dataset | Models | Seeds | Experiments |

|---|---:|---:|---:|

| N-BaIoT | 3 | 3 | 9 |

| MedBIoT | 3 | 3 | 9 |

| **Total** | | | **18** |



Every experiment completed successfully.



Each experiment used:



- 160,000 training rows

- 40,000 test rows



The results were written to:



`results/raw_metrics.csv`



---



## 7. Individual Experiment Results



### 7.1 N-BaIoT



| Model | Seed | Accuracy | Macro-F1 | FPR |

|---|---:|---:|---:|---:|

| Ensemble | 42 | 0.999850 | 0.999835 | 0.0000718 |

| Ensemble | 43 | 0.999875 | 0.999862 | 0.0000000 |

| Ensemble | 44 | 0.999950 | 0.999945 | 0.0000000 |

| Autoencoder | 42 | 0.979200 | 0.976859 | 0.0504811 |

| Autoencoder | 43 | 0.978750 | 0.976352 | 0.0517019 |

| Autoencoder | 44 | 0.979525 | 0.977220 | 0.0500503 |

| 1D-CNN | 42 | 0.999300 | 0.999229 | 0.0012207 |

| 1D-CNN | 43 | 0.999375 | 0.999311 | 0.0010771 |

| 1D-CNN | 44 | 0.999425 | 0.999366 | 0.0012207 |



### 7.2 MedBIoT



| Model | Seed | Accuracy | Macro-F1 | FPR |

|---|---:|---:|---:|---:|

| Ensemble | 42 | 0.998225 | 0.998225 | 0.0012000 |

| Ensemble | 43 | 0.999000 | 0.999000 | 0.0007000 |

| Ensemble | 44 | 0.998825 | 0.998825 | 0.0006000 |

| Autoencoder | 42 | 0.841500 | 0.839775 | 0.0547500 |

| Autoencoder | 43 | 0.853275 | 0.851922 | 0.0511500 |

| Autoencoder | 44 | 0.850875 | 0.849363 | 0.0489500 |

| 1D-CNN | 42 | 0.962750 | 0.962709 | 0.0040500 |

| 1D-CNN | 43 | 0.961725 | 0.961689 | 0.0077000 |

| 1D-CNN | 44 | 0.962050 | 0.962008 | 0.0048000 |



---



## 8. Aggregate Results Across Seeds



The following values are calculated over the three random seeds. Standard deviation uses the sample standard deviation across seeds.



### 8.1 N-BaIoT



| Rank | Model | Accuracy | Macro-F1 | FPR |

|---:|---|---:|---:|---:|

| 1 | **Ensemble** | **99.9892% Â± 0.0052%** | **99.9881% Â± 0.0057%** | **0.0024% Â± 0.0041%** |

| 2 | 1D-CNN | 99.9367% Â± 0.0063% | 99.9302% Â± 0.0069% | 0.1173% Â± 0.0083% |

| 3 | Autoencoder | 97.9158% Â± 0.0389% | 97.6810% Â± 0.0436% | 5.0744% Â± 0.0857% |



### 8.2 MedBIoT



| Rank | Model | Accuracy | Macro-F1 | FPR |

|---:|---|---:|---:|---:|

| 1 | **Ensemble** | **99.8683% Â± 0.0406%** | **99.8683% Â± 0.0406%** | **0.0833% Â± 0.0321%** |

| 2 | 1D-CNN | 96.2175% Â± 0.0524% | 96.2135% Â± 0.0522% | 0.5517% Â± 0.1928% |

| 3 | Autoencoder | 84.8550% Â± 0.6222% | 84.7020% Â± 0.6404% | 5.1617% Â± 0.2928% |



---



## 9. Model Ranking



The same ranking is obtained on both datasets:



### N-BaIoT



1. **Ensemble**

2. **1D-CNN**

3. **Autoencoder**



### MedBIoT



1. **Ensemble**

2. **1D-CNN**

3. **Autoencoder**



The ensemble therefore provides the strongest random-split baseline across both datasets.



---



## 10. Key Observations



### 10.1 Ensemble provides the strongest random-split performance



The ensemble achieves the highest Accuracy and Macro-F1 on both datasets.



On N-BaIoT:



- Accuracy: approximately 99.99%

- Macro-F1: approximately 99.99%

- Mean FPR: approximately 0.0024%



On MedBIoT:



- Accuracy: approximately 99.87%

- Macro-F1: approximately 99.87%

- Mean FPR: approximately 0.0833%



The very small standard deviations across the three seeds also indicate that the random-split results are highly stable.



### 10.2 1D-CNN is the second-best model



The CNN performs very strongly on N-BaIoT, reaching approximately 99.94% mean accuracy.



Its performance decreases on MedBIoT to approximately 96.22% mean accuracy.



The CNN nevertheless remains substantially stronger than the autoencoder under the random-split protocol.



### 10.3 Autoencoder performs substantially worse



The autoencoder has the lowest performance on both datasets.



Its mean accuracy is:



- N-BaIoT: approximately 97.92%

- MedBIoT: approximately 84.86%



The corresponding FPR is approximately 5% on both datasets.



This indicates that the current unsupervised reconstruction-based detector produces substantially more false positives than the supervised methods under the random-split protocol.



### 10.4 MedBIoT is more difficult for the current models



All three model arms show lower performance on MedBIoT compared with N-BaIoT.



The difference is particularly pronounced for:



- the 1D-CNN

- the autoencoder



The ensemble remains highly accurate on MedBIoT, but its accuracy also decreases slightly compared with N-BaIoT.



This demonstrates that the random-split baseline is not completely identical across datasets and that dataset characteristics affect model performance.



---



## 11. Important Interpretation of the Random-Split Results



The extremely high random-split scores should **not** be interpreted as evidence of generalization to previously unseen IoT devices.



The random protocol operates at the row level. Consequently, samples originating from the same physical device or device type can be present in both the training and test partitions.



This creates a substantially easier evaluation setting than Leave-Device-Out.



For example, the N-BaIoT ensemble achieves approximately 99.99% mean accuracy under the random split. This result demonstrates strong discrimination when training and testing samples are randomly drawn from the same overall device population.



It does **not** establish that the detector will achieve similar performance when an entirely unseen device is presented at test time.



The random-split baseline therefore serves as a reference point for the subsequent LDO experiments.



---



## 12. Random Split vs. Leave-Device-Out



The key purpose of establishing this baseline is to compare it against the stricter LDO evaluation.



Under LDO:



- one complete N-BaIoT physical device is held out for testing.

- one complete MedBIoT device type is held out for testing.



Therefore, the test device/device type is not represented in the training data.



The comparison between the two protocols will allow the project to quantify the effect of device-level distribution shift.



The expected research question is not simply:



> Which model has the highest accuracy?



Instead, the more important question is:



> How much does each detector's performance change when evaluation moves from random row-level splitting to unseen-device evaluation?



This comparison is central to assessing whether the apparently strong random-split results translate into device-level generalization.



---



## 13. Limitations of the Baseline



### 13.1 Random row-level splitting



The principal limitation is the potential overlap of device-specific distributions between training and testing.



This is intentional because Milestone 5 establishes a conventional random-split baseline, but it makes the protocol less demanding than LDO.



### 13.2 Controlled row caps



Each experiment uses:



- 160,000 training rows

- 40,000 test rows



These caps were applied consistently to all experiments to control computational cost and maintain comparable experimental conditions.



Therefore, these results are not necessarily equivalent to training each model on every available processed row.



### 13.3 Limited number of seeds



Three random seeds were used:



- 42

- 43

- 44



This provides an initial estimate of seed sensitivity but is not intended to be a comprehensive uncertainty analysis.



### 13.4 Autoencoder threshold



The autoencoder uses a 95th-percentile training-benign reconstruction threshold.



Its performance is therefore dependent on this thresholding strategy and should be interpreted within the defined experimental protocol.



---



## 14. Reproducibility



The complete batch experiment was executed using:



`scripts/run_milestone5.ps1`



The batch runner performs:



- 2 dataset evaluations

- 3 model evaluations per dataset

- 3 random seeds per model

- 18 total experiments



Configuration:



- training rows: 160,000

- test rows: 40,000

- test fraction: 0.20

- neural-network epochs: 5

- batch size: 256

- seeds: 42, 43, 44



Raw experiment results are stored in:



`results/raw_metrics.csv`



The complete execution log is stored in:



`results/milestone5_batch.log`



All 18 experiments completed successfully.



---



## 15. Scope of Milestone 5



Milestone 5 establishes the random-split performance baseline for all three planned detector families on both datasets.



The results demonstrate:



- strong supervised performance under random splitting.

- consistent ranking of the three model families.

- particularly strong ensemble performance.

- substantially weaker autoencoder performance.

- a measurable difference in difficulty between N-BaIoT and MedBIoT.



However, these results do not establish unseen-device generalization.



The subsequent LDO evaluation is therefore necessary to determine whether the high random-split performance is retained when the detector is evaluated on devices/device types that were not present during training.



---



## 16. Deliverables



Milestone 5 repository deliverables:



1. `results/raw_metrics.csv`

2. `docs/milestone-5/random-split-report.md`



Supporting reproducibility artifact:



`scripts/run_milestone5.ps1`



Execution log:



`results/milestone5_batch.log`



The raw dataset files and generated processed arrays remain excluded from version control because of their size.


