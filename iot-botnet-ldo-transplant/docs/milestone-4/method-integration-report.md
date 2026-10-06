\# Milestone 4 — Method Integration Report



\## 1. Objective



Milestone 4 establishes a unified training and evaluation infrastructure for the three planned IoT botnet detection model arms:



1\. Ensemble classifier:

&#x20;  - Random Forest

&#x20;  - Extra Trees

&#x20;  - Gradient Boosting



2\. Autoencoder:

&#x20;  - Unsupervised anomaly detection

&#x20;  - Trained only using benign traffic from the training data



3\. 1D Convolutional Neural Network:

&#x20;  - Supervised binary classification



The infrastructure supports both random train/test evaluation and Leave-Device-Out (LDO) evaluation.



The purpose of this milestone is to verify that all model arms can be trained and evaluated using a common interface, common preprocessing rules, common metrics, and reproducible logging.



\---



\## 2. Data Source



Milestone 4 uses the leakage-safe unscaled datasets generated from the Milestone 3 canonical 100-feature schema.



The data are stored locally under:



`data/processed\_unscaled/`



Each LDO unit is stored as one `.npy` file containing:



\- 100 canonical feature columns

\- 1 binary label column



Labels are:



\- `0` = benign / legitimate

\- `1` = attack / malicious



The processed LDO units are:



\### N-BaIoT



\- Danmini\_Doorbell

\- Ecobee\_Thermostat

\- Ennio\_Doorbell

\- Philips\_B120N10\_Baby\_Monitor

\- Provision\_PT\_737E\_Security\_Camera

\- Provision\_PT\_838\_Security\_Camera

\- Samsung\_SNH\_1011\_N\_Webcam

\- SimpleHome\_XCS7\_1002\_WHT\_Security\_Camera

\- SimpleHome\_XCS7\_1003\_WHT\_Security\_Camera



\### MedBIoT



\- fan

\- light

\- switch



Thus, the evaluation infrastructure operates on 12 LDO units in total.



\---



\## 3. LDO Definition



The LDO protocol holds out one complete grouping unit as the test set.



For N-BaIoT:



\- one physical IoT device is one LDO unit.



For MedBIoT:



\- one device type (`fan`, `light`, or `switch`) is one LDO unit.



For a given LDO fold:



\- training data are taken from all groups except the held-out group.

\- the complete held-out group is used as the test set.



This prevents rows from the same held-out device/device-type from appearing in both training and testing.



\---



\## 4. Random Split Protocol



The random protocol performs a stratified row-level train/test split within the selected dataset.



Default configuration:



\- test fraction: 20%

\- random state: 42

\- stratification: enabled



Stratification preserves the binary class distribution between the training and test partitions.



Optional row caps are available in the command-line interface for smoke testing. These caps are not intended to represent final experimental settings.



\---



\## 5. Leakage-Safe Scaling



A key Milestone 4 requirement is that scaling must be fitted using training data only.



The original Milestone 3 processed arrays contain per-device staging normalization. Those files remain preserved under:



`data/processed/`



They are not used by the Milestone 4 training runner.



Instead, Milestone 3 now also generates unscaled canonical feature arrays under:



`data/processed\_unscaled/`



For every random split or LDO fold, Milestone 4 performs:



1\. load unscaled training and test data.

2\. fit `StandardScaler` using `X\_train` only.

3\. transform `X\_train` using the fitted scaler.

4\. transform `X\_test` using the same fitted scaler.



Therefore, the test partition does not contribute to the calculation of feature means or standard deviations.



This design is intended to avoid preprocessing leakage during the final evaluation pipeline.



\---



\## 6. Ensemble Method



The ensemble model is a soft-voting combination of three supervised classifiers:



\- Random Forest

\- Extra Trees

\- Gradient Boosting



The implementation is provided through:



`src/models/ensemble.py`



The training runner builds the ensemble with a configurable random seed and fits it using both binary classes in the supervised training set.



Predicted class probabilities are converted into binary predictions using a threshold of 0.5.



\---



\## 7. Autoencoder Method



The autoencoder is implemented as an unsupervised anomaly detector.



The implementation is provided through:



`src/models/autoencoder.py`



For each split/fold:



1\. the training split is created.

2\. only samples with `label = 0` are selected from the training data.

3\. the autoencoder is trained to reconstruct those benign samples.

4\. reconstruction error is calculated on the benign training data.

5\. the anomaly threshold is set from the training-benign reconstruction error distribution.

6\. the trained model is then evaluated on the complete test set, including both benign and attack samples.



The default threshold is the 95th percentile of training-benign reconstruction error.



A test label is never used to determine the threshold.



A test sample is classified as attack when its reconstruction error is greater than or equal to the learned threshold.



This preserves the unsupervised nature of the autoencoder training procedure.



\---



\## 8. 1D-CNN Method



The 1D-CNN is implemented as a supervised binary classifier.



The implementation is provided through:



`src/models/cnn.py`



The 100-dimensional feature vector is reshaped to:



`(100, 1)`



for convolutional processing.



The current prototype consists of:



\- 1D convolution layer

\- max-pooling layer

\- flatten layer

\- dense hidden layer

\- sigmoid binary-output layer



The classifier is trained using the binary training labels and predicts attack probability for the test samples.



Training epochs and batch size are configurable from the command line.



\---



\## 9. Common Evaluation Metrics



All three model arms use the same evaluation metrics.



\### Accuracy



Overall fraction of correctly classified samples.



\### Macro-F1



F1 score is calculated independently for both classes and then averaged.



Macro-F1 gives equal importance to benign and attack classes.



\### False Positive Rate



FPR is defined as:



`FPR = FP / (FP + TN)`



where:



\- `TN` = benign samples correctly identified as benign

\- `FP` = benign samples incorrectly identified as attacks



The project uses:



\- class `0` = benign

\- class `1` = attack



\---



\## 10. Unified Training Interface



The main Milestone 4 runner is:



`src/train.py`



It accepts:



\- model type

\- dataset

\- split protocol

\- optional LDO fold

\- random state

\- neural-network training parameters

\- optional smoke-test row caps

\- output CSV path



Supported model values:



\- `ensemble`

\- `autoencoder`

\- `cnn`



Supported split values:



\- `random`

\- `ldo`



This provides one consistent command-line interface for all three method arms.



\---



\## 11. Result Logging



Evaluation results are written to CSV.



The logging schema is:



\- model

\- dataset

\- split\_type

\- fold

\- random\_state

\- train\_rows

\- test\_rows

\- train\_benign

\- train\_attack

\- test\_benign

\- test\_attack

\- accuracy

\- macro\_f1

\- fpr



The current smoke-test deliverable is:



`results/smoke\_test\_results.csv`



Generated experiment results can also be written to:



`results/raw\_metrics.csv`



The `results/` directory is ignored by default except for the required smoke-test CSV.



\---



\## 12. Smoke Test



A small N-BaIoT LDO smoke test was performed using:



\- held-out fold: `Danmini\_Doorbell`

\- training-row cap: 2,000

\- test-row cap: 1,000

\- random state: 42



The same data split and scaling procedure were used for all three model arms.



The neural-network models were deliberately limited to 2 epochs for infrastructure validation.



\### Smoke-test results



| Model | Accuracy | Macro-F1 | FPR |

|---|---:|---:|---:|

| 1D-CNN | 0.997000 | 0.996616 | 0.003021 |

| Ensemble | 0.996000 | 0.995491 | 0.003021 |

| Autoencoder | 0.332000 | 0.250365 | 0.000000 |



These values are \*\*smoke-test results only\*\*.



They are not final research results and must not be interpreted as the performance of the proposed detectors on the complete datasets.



The smoke test verifies that:



\- the datasets load correctly.

\- the LDO fold is constructed correctly.

\- training/test dimensions are correct.

\- scaling occurs using training data.

\- all three model arms train successfully.

\- predictions are generated.

\- Accuracy, Macro-F1, and FPR are calculated.

\- results are written to the required CSV format.



\---



\## 13. Reproducibility



The default random seed is:



`42`



The training runner exposes the seed through:



`--random-state`



The Ensemble uses the supplied random state.



The neural-network models use TensorFlow/Keras deterministic seed initialization through the supplied random state.



Smoke-test row caps are explicitly configurable and are intended only for rapid infrastructure verification.



\---



\## 14. Milestone 3 Compatibility Note



Milestone 3 originally produced per-device standardized arrays in:



`data/processed/`



Those outputs are retained as the original Milestone 3 staging artifacts.



For Milestone 4, additional unscaled arrays were generated in:



`data/processed\_unscaled/`



This separation allows Milestone 4 to perform the required training-only scaler fitting independently for every random split or LDO fold.



The unscaled arrays are generated data artifacts and are intentionally excluded from version control because of their size. The preprocessing code required to reproduce them is tracked in:



`src/data/prep.py`



\---



\## 15. Scope of Milestone 4



This milestone establishes and validates the training/evaluation infrastructure.



The current smoke-test execution does not constitute the final experimental campaign.



The full research evaluation should subsequently run the required random-split and LDO experiments across the selected datasets and model arms, using the leakage-safe training-only scaling procedure established here.



Final research conclusions should be based only on the complete planned experiment set and its logged results.



\---



\## 16. Deliverables



Milestone 4 repository deliverables:



1\. `src/train.py`

2\. `results/smoke\_test\_results.csv`

3\. `docs/milestone-4/method-integration-report.md`



Supporting preprocessing changes required for leakage-safe execution:



`src/data/prep.py`



The generated directory:



`data/processed\_unscaled/`



is intentionally excluded from version control.

