| model | test subset | images | both found | both upper OK | PCK@0.1 | extra dets/img | pose AP |
|---|---|---|---|---|---|---|---|
| base | h4d_mma | 342 | 84.2% | 81.3% | 90.5% | 1.83 | 0.5809 |
| base | all | 1135 | 69.9% | 66.8% | 79.9% | 0.94 |  |
| base | h4d_grappling | 576 | 76.7% | 73.8% | 84.3% | 0.73 | 0.5172 |
| base | vicos_bjj | 217 | 29.0% | 25.4% | 51.1% | 0.11 | 0.2229 |
| finetuned | h4d_mma | 342 | 90.9% | 90.9% | 94.0% | 0.00 | 0.7561 |
| finetuned | all | 1135 | 79.1% | 79.1% | 86.6% | 0.02 |  |
| finetuned | h4d_grappling | 576 | 88.9% | 88.9% | 92.5% | 0.01 | 0.7571 |
| finetuned | vicos_bjj | 217 | 34.6% | 34.6% | 58.6% | 0.06 | 0.153 |
| rtmo_m | h4d_mma | 342 | 88.0% | 85.7% | 92.7% | 3.97 |  |
| rtmo_m | all | 1135 | 80.3% | 76.2% | 85.8% | 2.17 |  |
| rtmo_m | h4d_grappling | 576 | 84.2% | 77.6% | 88.8% | 1.80 |  |
| rtmo_m | vicos_bjj | 217 | 57.6% | 57.6% | 66.8% | 0.29 |  |
| finetuned_onnx | h4d_mma | 342 | 90.9% | 90.9% | 94.0% | 0.00 |  |
| finetuned_onnx | all | 1135 | 79.3% | 79.3% | 86.5% | 0.02 |  |
| finetuned_onnx | h4d_grappling | 576 | 88.9% | 88.9% | 92.5% | 0.01 |  |
| finetuned_onnx | vicos_bjj | 217 | 35.5% | 35.5% | 58.3% | 0.06 |  |
