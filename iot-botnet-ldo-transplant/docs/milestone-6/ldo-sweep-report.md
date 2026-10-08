\# Milestone 6 â€” Leave-Device-Out Evaluation Report



\## 1. Objective



Milestone 6 evaluates the generalization of the three established IoT botnet detection approaches under \*\*Leave-Device-Out (LDO)\*\* evaluation.



Unlike the Milestone 5 random row-level split, LDO ensures that the held-out device or device type is completely excluded from model training. This provides a stricter test of whether a detector can generalize to previously unseen device behavior.



The three evaluated model arms are:



1\. \*\*Ensemble\*\* â€” Random Forest + Extra Trees + Gradient Boosting

2\. \*\*Autoencoder\*\* â€” unsupervised anomaly detector trained only on benign training traffic

3\. \*\*1D-CNN\*\* â€” supervised binary classifier



Milestone 6 evaluates:



\- 9 N-BaIoT devices

\- 3 MedBIoT device types

\- 3 models

\- 3 random seeds



This produces:



\\\[

(9 + 3) \\times 3 \\times 3 = 108

\\]



LDO experiments.



Combined with the 18 Milestone 5 random-split baseline runs, the final results file contains \*\*126 experiment records\*\*.



\---



\## 2. Experimental Configuration



The LDO experiments used the following configuration:



| Parameter | Configuration |

|---|---|

| Evaluation | Leave-Device-Out |

| Training row cap | 160,000 |

| Test row cap | 40,000 |

| Random seeds | 42, 43, 44 |

| CNN epochs | 5 |

| Autoencoder epochs | 5 |

| Batch size | 256 |

| Scaling | StandardScaler |

| Scaling fit | Training data only |

| N-BaIoT held-out units | 9 physical devices |

| MedBIoT held-out units | fan, light, switch |

| Models | Ensemble, Autoencoder, 1D-CNN |



For every LDO fold, all data belonging to the held-out device/device type were excluded from training. The scaler was also fitted only on the training data before transforming the held-out test data.



The row caps were applied after separating the training groups from the held-out group. Stratified sampling was used when a cap was required.



\---



\## 3. Dataset Coverage



\### N-BaIoT



All nine staged N-BaIoT devices were evaluated as separate LDO folds:



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



The three available staged device types were evaluated:



\- fan

\- light

\- switch



\---



\## 4. LDO Aggregate Results



The following values are calculated across the three seeds and all LDO folds for each dataset/model combination.



\### N-BaIoT



| Model | Accuracy Mean Â± SD | Macro-F1 Mean Â± SD | FPR Mean Â± SD |

|---|---:|---:|---:|

| Ensemble | 0.998331 Â± 0.003675 | 0.998089 Â± 0.004263 | 0.004632 Â± 0.011515 |

| CNN | 0.996698 Â± 0.007514 | 0.996088 Â± 0.008923 | 0.009243 Â± 0.023736 |

| Autoencoder | 0.956083 Â± 0.049781 | 0.940752 Â± 0.060935 | 0.124043 Â± 0.126761 |



\### MedBIoT



| Model | Accuracy Mean Â± SD | Macro-F1 Mean Â± SD | FPR Mean Â± SD |

|---|---:|---:|---:|

| Ensemble | 0.986106 Â± 0.014143 | 0.986095 Â± 0.014159 | 0.003211 Â± 0.002154 |

| CNN | 0.957903 Â± 0.013764 | 0.957834 Â± 0.013844 | 0.010172 Â± 0.006670 |

| Autoencoder | 0.832111 Â± 0.053415 | 0.828419 Â± 0.059667 | 0.053811 Â± 0.005661 |



The Ensemble is the highest-performing model on both datasets under LDO evaluation.



\---



\## 5. Random-Split vs LDO Degradation



Milestone 5 provides the random row-level baseline. Degradation is calculated as:



\\\[

\\Delta = \\text{Random-Split Mean} - \\text{LDO Mean}

\\]



A positive Accuracy or Macro-F1 delta therefore indicates that the random split produced a higher score than the stricter LDO evaluation.



\### N-BaIoT



| Model | Accuracy Random | Accuracy LDO | Î” Accuracy | Macro-F1 Random | Macro-F1 LDO | Î” Macro-F1 | FPR Random | FPR LDO | Î” FPR |

|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

| Ensemble | 0.999892 | 0.998331 | 0.001560 | 0.999881 | 0.998089 | 0.001792 | 0.000024 | 0.004632 | -0.004608 |

| CNN | 0.999367 | 0.996698 | 0.002669 | 0.999302 | 0.996088 | 0.003214 | 0.001173 | 0.009243 | -0.008070 |

| Autoencoder | 0.979158 | 0.956083 | 0.023075 | 0.976810 | 0.940752 | 0.036058 | 0.050744 | 0.124043 | -0.073299 |



\### MedBIoT



| Model | Accuracy Random | Accuracy LDO | Î” Accuracy | Macro-F1 Random | Macro-F1 LDO | Î” Macro-F1 | FPR Random | FPR LDO | Î” FPR |

|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

| Ensemble | 0.998683 | 0.986106 | 0.012578 | 0.998683 | 0.986095 | 0.012588 | 0.000833 | 0.003211 | -0.002378 |

| CNN | 0.962175 | 0.957903 | 0.004272 | 0.962135 | 0.957834 | 0.004302 | 0.005517 | 0.010172 | -0.004656 |

| Autoencoder | 0.848550 | 0.832111 | 0.016439 | 0.847020 | 0.828419 | 0.018601 | 0.051617 | 0.053811 | -0.002194 |



For FPR, a negative delta means that the LDO FPR is higher than the random-split FPR.



\---



\## 6. Key Observations



\### 6.1 Ensemble provides the strongest overall LDO robustness



The Ensemble achieves the best mean Accuracy and Macro-F1 on both datasets:



\- N-BaIoT: \*\*99.83% Accuracy\*\*, \*\*99.81% Macro-F1\*\*

\- MedBIoT: \*\*98.61% Accuracy\*\*, \*\*98.61% Macro-F1\*\*



Its performance remains particularly stable on N-BaIoT, where the Accuracy decreases by only approximately \*\*0.16 percentage points\*\* from the random split.



The Ensemble therefore demonstrates the strongest generalization among the three evaluated approaches.



\---



\### 6.2 CNN remains competitive under unseen-device evaluation



The CNN performs substantially better than the Autoencoder and remains close to the Ensemble on N-BaIoT.



Its N-BaIoT Accuracy decreases from \*\*99.94%\*\* under the random split to \*\*99.67%\*\* under LDO, a degradation of approximately \*\*0.27 percentage points\*\*.



On MedBIoT, the degradation is approximately \*\*0.43 percentage points\*\*.



Although the CNN has higher FPR than the Ensemble, its Accuracy and Macro-F1 remain strong under unseen-device evaluation.



\---



\### 6.3 Autoencoder is substantially more sensitive to device distribution shift



The Autoencoder shows the largest degradation in most Accuracy and Macro-F1 comparisons.



On N-BaIoT:



\- Accuracy decreases from \*\*97.92% â†’ 95.61%\*\*

\- Macro-F1 decreases from \*\*97.68% â†’ 94.08%\*\*

\- FPR increases from \*\*5.07% â†’ 12.40%\*\*



The approximately \*\*7.33 percentage-point increase in FPR\*\* is particularly important.



This indicates that benign traffic from an unseen device can differ sufficiently from the benign training distribution to produce substantially more false anomaly detections.



The effect is also visible in the large N-BaIoT FPR standard deviation (\*\*0.126761\*\*), indicating considerable variation between held-out devices.



\---



\### 6.4 The Autoencoder FPR increase is not universal



The results do not support the claim that LDO always causes an Autoencoder FPR spike.



On MedBIoT:



\- Random-split FPR: \*\*5.16%\*\*

\- LDO FPR: \*\*5.38%\*\*



The difference is only approximately \*\*0.22 percentage points\*\*.



Therefore, the stronger conclusion is that the Autoencoder is \*\*more sensitive to device-specific distribution shifts\*\*, with the effect being particularly severe on N-BaIoT.



\---



\## 7. Difficult Held-Out Devices



Fold-level analysis reveals several devices where performance deteriorates substantially.



\### 7.1 MedBIoT â€” switch



The `switch` device type is the clearest difficult MedBIoT fold because all three models perform worse than on the other two device types.



| Model | Accuracy | Macro-F1 | FPR |

|---|---:|---:|---:|

| Autoencoder | 0.781683 | 0.772861 | 0.049200 |

| CNN | 0.940067 | 0.939889 | 0.005733 |

| Ensemble | 0.967317 | 0.967285 | 0.001700 |



The cross-model degradation makes `switch` a meaningful example of a device distribution that is difficult to generalize to.



\---



\### 7.2 N-BaIoT â€” SimpleHome\_XCS7\_1002\_WHT\_Security\_Camera



This device is the clearest difficult N-BaIoT fold across all three models.



| Model | Accuracy | Macro-F1 | FPR |

|---|---:|---:|---:|

| Autoencoder | 0.961617 | 0.954176 | 0.119913 |

| CNN | 0.980050 | 0.976408 | 0.062067 |

| Ensemble | 0.988392 | 0.986482 | 0.036213 |



All three approaches show noticeable degradation on this held-out device, although the Ensemble remains substantially more robust than the other two models.



\---



\### 7.3 Ecobee â€” Autoencoder-specific failure



Ecobee\_Thermostat demonstrates an important model-specific failure mode.



The Autoencoder achieves approximately \*\*94.81% Accuracy\*\*, but its mean FPR reaches \*\*44.33%\*\*.



In contrast:



\- CNN Accuracy: \*\*99.96%\*\*

\- Ensemble Accuracy: \*\*99.99%\*\*



This indicates that the poor Autoencoder performance is not simply caused by the device being universally difficult. Instead, it suggests that the Autoencoder's learned representation of benign traffic is particularly sensitive to this device's distribution.



\---



\## 8. Interpretation



The comparison between random row-level splitting and LDO demonstrates why evaluation methodology matters for IoT intrusion detection.



Under a random split, observations from the same device can appear in both training and test sets. This allows the model to learn device-specific traffic characteristics that may also be present in the test data.



LDO removes this overlap at the device level.



The resulting degradation is therefore evidence of a generalization gap rather than simply a reduction in training data.



The results indicate three distinct behaviors:



1\. \*\*Ensemble:\*\* strongest and most consistent unseen-device performance.

2\. \*\*CNN:\*\* strong supervised generalization, with moderate degradation.

3\. \*\*Autoencoder:\*\* substantially higher sensitivity to device-specific benign traffic distributions, particularly on N-BaIoT.



This supports the use of device-aware evaluation when claiming practical generalization of IoT botnet detectors.



\---



\## 9. Limitations



Several limitations should be considered when interpreting the results.



\### Dataset and feature limitations



The experiments use the standardized 100-feature representation established during Milestone 3. Although this provides a common schema, the original datasets use different feature naming and statistical terminology.



The experiments therefore establish comparative behavior under the adopted standardized representation rather than proving equivalence between the original feature-generation pipelines.



\### Computational limits



Each experiment used a maximum of 160,000 training rows and 40,000 test rows. These caps make the 108-run LDO sweep computationally manageable, but they do not use every available row when a group exceeds the cap.



\### Model configuration



The models use the fixed configurations implemented in the Milestone 4 training infrastructure. The results should therefore be interpreted as a comparison of these established implementations rather than an exhaustive hyperparameter optimization study.



\### Cross-dataset transfer



Milestone 6 evaluates unseen-device/device-type generalization \*\*within each dataset\*\*. It does not by itself establish cross-dataset transfer from N-BaIoT to MedBIoT or vice versa.



\---



\## 10. Conclusion



Milestone 6 provides the required Leave-Device-Out evaluation of the three IoT botnet detection approaches.



The central finding is that \*\*device-aware evaluation produces a substantially more realistic picture of detector generalization than random row-level splitting\*\*.



The Ensemble is the strongest overall model, achieving:



\- \*\*99.83% N-BaIoT Accuracy\*\*

\- \*\*98.61% MedBIoT Accuracy\*\*



under LDO evaluation.



The CNN remains competitive, while the Autoencoder exhibits substantially greater sensitivity to unseen-device distributions. On N-BaIoT, its FPR increases from approximately \*\*5.07% under random splitting to 12.40% under LDO\*\*, with particularly severe device-specific failures.



The difficult-fold analysis further demonstrates that generalization is not uniform across devices. The MedBIoT `switch` type and N-BaIoT `SimpleHome\_XCS7\_1002\_WHT\_Security\_Camera` are challenging across multiple models, while the `Ecobee\_Thermostat` results expose a particularly severe Autoencoder-specific false-positive problem.



Overall, the Milestone 6 results strengthen the central research question of the project: \*\*high random-split performance does not necessarily imply robust detection on previously unseen IoT devices.\*\*
