import os
import json
import logging

from os.path import join, isdir, basename, splitext
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm
from typing import cast

from src.common_utils import parse_args, dict_to_tuple

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "perturbation_ground_truth_generator.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def get_num_range_perturbation_ground_truth(perturbation_info, vul_lines):
    perturbed_line, perturbation_type, cmp_with = perturbation_info
    perturbed_line = int(perturbed_line)
    cmp_with = 0 if cmp_with == "0" else -1
    if perturbation_type == "FP":
        return vul_lines
    return [ln for ln in vul_lines if ln != perturbed_line]

def get_sensi_perturbation_ground_truth(perturbation_info, vul_lines):
    perturbed_line, perturbation_type = perturbation_info
    perturbed_line = int(perturbed_line)
    if perturbation_type == "FP":
        return vul_lines
    return [ln + 1 for ln in vul_lines if ln != perturbed_line]

def get_dealloc_perturbation_ground_truth(perturbation_info, vul_lines):
    perturbed_ln, perturbation_type, impacted_line_info = perturbation_info
    impacted_line_info = impacted_line_info.split("+")
    impacted_ln = int(impacted_line_info[0])
    increase_for_line, increase_after_line = 0, 0
    if len(impacted_line_info) > 1:
        increase_for_line = int(impacted_line_info[1])
    if len(impacted_line_info) > 2:
        increase_after_line = int(impacted_line_info[2])
    new_vul_lines = [ln if ln < impacted_ln else (ln + increase_for_line) if ln == impacted_ln else (ln + increase_after_line) for ln in vul_lines]
    impacted_ln += increase_for_line
    if perturbation_type == "FR":
        return [ln for ln in new_vul_lines if ln != impacted_ln]
    return new_vul_lines

def get_perturbation_ground_truth(perturbation_info, feat_name, vul_lines):
    perturbation_info = perturbation_info.split("_")[1:]
    if "under" in feat_name:
        return get_num_range_perturbation_ground_truth(perturbation_info, vul_lines)
    if "sensi" in feat_name:
        return get_sensi_perturbation_ground_truth(perturbation_info, vul_lines)
    if "free" in feat_name:
        return get_dealloc_perturbation_ground_truth(perturbation_info, vul_lines)
    perturbation_type, impacted_line = perturbation_info[-2:]
    if perturbation_type == "FP":
        return vul_lines
    impacted_line = int(impacted_line)
    return [ln for ln in vul_lines if ln != impacted_line]

if __name__ == "__main__":
    __args = parse_args()
    config = cast(DictConfig, OmegaConf.load(__args.config))
    repo_root = join("..", config.repo_root)
    data_folder = join(repo_root, config.data_folder)
    dataset_root = join(data_folder, config.dataset.name)
    init_log()

    source_root_path = join(dataset_root, config.source_root_folder)

    ground_truth_path = join(dataset_root, config.ground_truth_filename)
    logging.info(f"Reading ground truth from {ground_truth_path}...")
    with open(ground_truth_path, "r") as rfi:
        ground_truth = json.load(rfi)
    logging.info("Completed.")
    
    perturbation_result_path = join(dataset_root, config.perturbation_result_filename)
    logging.info(f"Reading perturbation results from {perturbation_result_path}...")
    with open(perturbation_result_path, "r") as rfi:
        perturbation_results = json.load(rfi)
    logging.info("Completed.")

    perturbation_ground_truth = dict()

    logging.info(f"Generating pertrubation ground truth...")
    for cpp_path, perturbations in tqdm(perturbation_results.items(), total=len(perturbation_results), desc=f"Source files"):
        if len(perturbations) == 0:
            continue
        filename, extension = splitext(basename(cpp_path))
        vul_lines = []
        if cpp_path in ground_truth:
            vul_lines = ground_truth[cpp_path]
        with open(join(source_root_path, cpp_path), "r") as rfi:
            src_lines = rfi.readlines()
        for entry in perturbations:
            feat_name, perturbed_file_paths = dict_to_tuple(entry)
            feat_dir = join(dataset_root, feat_name)
            if feat_dir not in perturbation_ground_truth:
                perturbation_ground_truth[feat_dir] = dict()
                perturbation_ground_truth[feat_dir][cpp_path] = vul_lines
            if len(perturbed_file_paths) == 0:
                continue
            for perturbed_file_path in perturbed_file_paths:
                with open(join(feat_dir, perturbed_file_path), "r") as rfi:
                    perturbed_src_lines = rfi.readlines()
                perturbed_filename, perturbed_extension = splitext(basename(perturbed_file_path))
                new_vul_lines = get_perturbation_ground_truth(perturbed_filename.replace(filename, ""), feat_name, vul_lines)
                if len(new_vul_lines) == 0:
                    continue
                perturbation_ground_truth[feat_dir][perturbed_file_path] = new_vul_lines
    logging.info("Completed.")
    for feat_dir, ground_truth in perturbation_ground_truth.items():
        feat_ground_truth_path = join(feat_dir, config.ground_truth_filename)
        logging.info(f"Writing ground truth to {feat_ground_truth_path}...")
        with open(feat_ground_truth_path, "w") as wfi:
            json.dump(ground_truth, wfi, indent=2)
        logging.info("Completed.")