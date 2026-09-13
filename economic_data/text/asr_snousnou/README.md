---
dataset_info:
  features:
  - name: file
    dtype:
      audio:
        sampling_rate: 16000
  - name: text
    dtype: string
  splits:
  - name: train
    num_bytes: 319658.6666666667
    num_examples: 6
  - name: validation
    num_bytes: 53276.77777777778
    num_examples: 1
  - name: test
    num_bytes: 106553.55555555556
    num_examples: 2
  download_size: 484422
  dataset_size: 479489.00000000006
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: validation
    path: data/validation-*
  - split: test
    path: data/test-*
---
