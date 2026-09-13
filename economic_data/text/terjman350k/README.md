---
dataset_info:
  features:
  - name: english
    dtype: string
  - name: darija_Arab
    dtype: string
  - name: darija_Latn
    dtype: string
  - name: dataset_source
    dtype: string
  - name: id
    dtype: string
  - name: role
    dtype: string
  - name: darija_tokens
    dtype: int64
  - name: subtopic
    dtype: string
  - name: topic
    dtype: string
  - name: annotator_dialect
    dtype: string
  splits:
  - name: train
    num_bytes: 400022028.89170796
    num_examples: 354112
  - name: test
    num_bytes: 143518
    num_examples: 850
  download_size: 213959197
  dataset_size: 400165546.89170796
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
---
