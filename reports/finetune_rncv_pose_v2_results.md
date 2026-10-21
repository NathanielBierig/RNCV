| model | test subset | images | both found | both upper OK | PCK@0.1 | extra dets/img | pose AP |
|---|---|---|---|---|---|---|---|
| base | h4d_mma | 342 | 84.8% | 82.8% | 90.4% | 2.35 | 0.5666 |
| base | all | 1135 | 70.8% | 68.5% | 80.1% | 1.26 |  |
| base | h4d_grappling | 576 | 77.6% | 75.2% | 84.8% | 1.05 | 0.51 |
| base | vicos_bjj | 217 | 30.4% | 28.6% | 50.9% | 0.11 | 0.2253 |
| finetuned | h4d_mma | 342 | 92.1% | 92.1% | 94.2% | 0.00 | 0.7645 |
| finetuned | all | 1135 | 77.8% | 77.8% | 85.4% | 0.01 |  |
| finetuned | h4d_grappling | 576 | 88.4% | 88.4% | 91.6% | 0.01 | 0.7621 |
| finetuned | vicos_bjj | 217 | 27.2% | 27.2% | 54.2% | 0.01 | 0.1346 |
| rtmo_m | h4d_mma | 342 | 88.0% | 85.7% | 92.7% | 3.97 |  |
| rtmo_m | all | 1135 | 80.3% | 76.2% | 85.8% | 2.17 |  |
| rtmo_m | h4d_grappling | 576 | 84.2% | 77.6% | 88.8% | 1.80 |  |
| rtmo_m | vicos_bjj | 217 | 57.6% | 57.6% | 66.8% | 0.29 |  |
| finetuned_onnx | h4d_mma | 342 | 93.3% | 93.3% | 94.5% | 0.00 |  |
| finetuned_onnx | all | 1135 | 79.8% | 79.8% | 86.2% | 0.01 |  |
| finetuned_onnx | h4d_grappling | 576 | 90.1% | 90.1% | 92.9% | 0.01 |  |
| finetuned_onnx | vicos_bjj | 217 | 31.3% | 31.3% | 55.0% | 0.01 |  |
