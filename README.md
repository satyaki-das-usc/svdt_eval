# svdt_eval
Repository for the framework to evaluate Software Vulnerability Detection Tools (SVDT)

# Replication data link

https://drive.google.com/drive/folders/13YmDeF0Fu7kHAalhfjXu03qaVfVyGroh?usp=sharing


# Required Schema

Raw cpp source code path: ```<dataset_root>/source-code```

Corresponding joern output path: ```<dataset_root>/csv```

Sample cpp source code path: ```<dataset_root>/source-code/000/063/114/CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_memcpy_03.c```

Corresponding sample joern output path: ```<dataset_root>/csv/000/063/114/CWE121_Stack_Based_Buffer_Overflow__CWE193_char_alloca_memcpy_03.c```


# For Unix

Run: ```PYTHONPATH="." python src/feature_detection.py```

Output: ```<dataset_root>/detection_result.json```

----------------------------------------------------------------------
This is optional. No need to run this if the previous step does not generate any errors.

Run: ```PYTHONPATH="." python src/ignore_list_feature_detection.py```

Output: ```<dataset_root>/ignore_list_detection_result.json```

----------------------------------------------------------------------
Merge content of ```<dataset_root>/detection_result.json``` and ```<dataset_root>/ignore_list_detection_result.json``` then write the merged detection results to ```<dataset_root>/detection_result.json```.

----------------------------------------------------------------------
Run: ```PYTHONPATH="." python src/targeted_perturbation.py```

Output: ```<dataset_root>/perturbation_result.json``` and ```<dataset_root>/<feat_name>/source-code``` for every `feat_name` in the list of VFs where the pertrubed samples are stored.

----------------------------------------------------------------------
Run: ```PYTHONPATH="." python src/perturbation_ground_truth_generator.py```

Output: ```<dataset_root>/<feat_name>/ground_truth.json``` for every `feat_name` in the list of VFs containing the ground truth of the perturbed samples.


# For Windows
```$env:PYTHONPATH = "."```

----------------------------------------------------------------------
Run: ```python src/feature_detection.py```

Output: ```<dataset_root>/detection_result.json```

----------------------------------------------------------------------
This is optional. No need to run this if the previous step does not generate any errors.

Run: ```python src/ignore_list_feature_detection.py```

Output: ```<dataset_root>/ignore_list_detection_result.json```

----------------------------------------------------------------------
Merge content of ```<dataset_root>/detection_result.json``` and ```<dataset_root>/ignore_list_detection_result.json``` then write the merged detection results to ```<dataset_root>/detection_result.json```.

----------------------------------------------------------------------
Run: ```python src/targeted_perturbation.py```

Output: ```<dataset_root>/perturbation_result.json``` and ```<dataset_root>/<feat_name>/source-code``` for every `feat_name` in the list of VFs where the pertrubed samples are stored. Generate ```<dataset_root>/<feat_name>/unperturbed_file_list.json``` from ```<dataset_root>/perturbation_result.json``` and list all the files containing perturbations for `feat_name`.

----------------------------------------------------------------------
Run: ```python src/perturbation_ground_truth_generator.py```

Output: ```<dataset_root>/<feat_name>/ground_truth.json``` for every `feat_name` in the list of VFs containing the ground truth of the perturbed samples.


After obtaining detectors predictions save the predictions in ```<detector_name>/<feat_name>/filewise_pred_mapping.json``` and copy ```<dataset_root>/<feat_name>/unperturbed_file_list.json``` to ```<detector_name>/<feat_name>/unperturbed_file_list.json```. No need to copy `unperturbed_file_list.json` for SFs.

# For Unix

Run: ```PYTHONPATH="." python src/solution_evaluation_vf.py -d DeepDFA```

Output: ```<detector_name>_vf_rq3.csv```

----------------------------------------------------------------------
Run: ```PYTHONPATH="." python src/solution_evaluation_sf.py -d DeepDFA```

Output: ```<detector_name>_sf_rq2.csv```


# For Windows
```$env:PYTHONPATH = "."```

----------------------------------------------------------------------
Run: ```python src/solution_evaluation_vf.py -d DeepDFA```

Output: ```<detector_name>_vf_rq3.csv```

----------------------------------------------------------------------
Run: ```python src/solution_evaluation_sf.py -d DeepDFA```

Output: ```<detector_name>_sf_rq2.csv```
