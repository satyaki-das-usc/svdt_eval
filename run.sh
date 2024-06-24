#!/bin/bash

export PATH="/media/satyaki/22cce3a2-7e84-4401-9b92-07e2fbeec5561/research/miniconda3/bin:$PATH"

conda remove --name svdt_eval --all
conda create -n svdt_eval python=3.10
conda activate svdt_eval
# conda install pytorch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 pytorch-cuda=11.7 -c pytorch -c nvidia
PIP_CACHE_DIR=/media/satyaki/22cce3a2-7e84-4401-9b92-07e2fbeec5561/.cache/pip TMPDIR=/media/satyaki/22cce3a2-7e84-4401-9b92-07e2fbeec5561/pip_tmp pip install -r requirements.txt
PIP_CACHE_DIR=/media/satyaki/22cce3a2-7e84-4401-9b92-07e2fbeec5561/.cache/pip TMPDIR=/media/satyaki/22cce3a2-7e84-4401-9b92-07e2fbeec5561/pip_tmp pip install --upgrade jupyter ipywidgets


# For Unix

PYTHONPATH="." python src/feature_detection.py
PYTHONPATH="." python src/ignore_list_feature_detection.py
PYTHONPATH="." python src/targeted_perturbation.py
PYTHONPATH="." python src/perturbation_ground_truth_generator.py

# For Windows
$env:PYTHONPATH = "."
python src/feature_detection.py
python src/ignore_list_feature_detection.py
python src/targeted_perturbation.py
python src/perturbation_ground_truth_generator.py