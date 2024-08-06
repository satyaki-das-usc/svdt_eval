# svdt_eval
Repository for the framework to evaluate Software Vulnerability Detection Tools (SVDT)

# Replication data link

https://drive.google.com/file/d/1J5d06p1_-ZTrNonwmM4oAFIoZaABCPkw/view?usp=sharing


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

After obtaining detectors predictions

# For Unix

PYTHONPATH="." python src/solution_evaluation_vf.py
PYTHONPATH="." python src/solution_evaluation_sf.py

# For Windows
$env:PYTHONPATH = "."
python src/solution_evaluation_vf.py
python src/solution_evaluation_sf.py