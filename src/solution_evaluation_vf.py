import os
import json
import logging
import pandas as pd

from argparse import ArgumentParser
from os.path import join, exists, isdir, isfile, basename, dirname, splitext

data_folder = ""
dataset_root = ""
source_root_path = ""
csv_path = ""

file_path_key = ""
unit_id_key = ""
location_key = ""
target_key = ""
prediction_key = ""
name_feat = ""
filewise_pred_mapping_path = ""
detector_name = ""

feature_name_dict = {
    "incorr_calc_buff_size": "Incorrect Calculation of Buffer Size",
    "buff_access_src_size": "Buffer Access Using Size of Source Buffer",
    "off_by_one": "Off-by-one Error",
    "buff_overread": "Buffer Over-read",
    "double_free": "Double-Free",
    "use_after_free": "Use-After-Free",
    "buff_underwrite": "Buffer Underwrite",
    "buff_underread": "Buffer Under-read",
    "sensi_read": "Sensitive Read API",
    "sensi_write": "Sensitive Write API"
}
FR_success_cnt_list = []
FR_all_cnt_list = []
FR_success_rate_list = []
FP_success_cnt_list = []
FP_all_cnt_list = []
FP_success_rate_list = []
feature_column_name_list = []

def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-u",
                            help="--unit_id_key",
                            help="Key denoting the unique id for the unit of prediction",
                            default="unit_id",
                            type=str)
    arg_parser.add_argument("-l",
                            help="--location_key",
                            help="Key denoting the location of the unit of prediction in source file",
                            default="loc",
                            type=str)
    arg_parser.add_argument("-t",
                            help="--target_key",
                            help="Key denoting the ground truth label of the unit of prediction",
                            default="target",
                            type=str)
    arg_parser.add_argument("-p",
                            help="--prediction_key",
                            help="Key denoting the prediction for the unit of prediction",
                            default="pred",
                            type=str)
    arg_parser.add_argument("-n",
                            help="--name_feat",
                            help="Name of feature",
                            default="SARD",
                            type=str)
    arg_parser.add_argument("-m",
                            help="--filewise_pred_mapping_path",
                            help="Name of feature",
                            default="pred",
                            type=str)
    arg_parser.add_argument("-d",
                            help="--detector_name",
                            help="Name of the DL-based vulnerability detector",
                            required=True,
                            default=None,
                            type=str)
    
    args = arg_parser.parse_args()

    return args

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "solution_evaluation_vf.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def get_FR_perturbation_response(file_results, perturbed_file_results, feature_name, perturbation_info):
    success_perturbations = []
    all_perturbations = []
    for pert_entry in perturbed_file_results:
        pert_loc = pert_entry[location_key]
        pert_unit_id = pert_entry[unit_id_key]
        pert_target = pert_entry[target_key]
        pert_pred = pert_entry[prediction_key]
        for entry in file_results:
            loc = entry[location_key]
            unit_id = entry[unit_id_key]
            if pert_loc != loc:
                continue
            target = entry[target_key]
            pred = entry[prediction_key]
            if pert_target == target:
                continue
            all_perturbations.append((f"{unit_id}::{loc}", f"{pert_unit_id}::{pert_loc}"))
            if pert_pred != pred:
                continue
            success_perturbations.append((f"{unit_id}::{loc}", f"{pert_unit_id}::{pert_loc}"))
    
    return success_perturbations, all_perturbations

def get_FP_perturbation_response(file_results, perturbed_file_results, feature_name, perturbation_info):
    success_perturbations = []
    all_perturbations = []
    for pert_entry in perturbed_file_results:
        pert_loc = pert_entry[location_key]
        pert_unit_id = pert_entry[unit_id_key]
        pert_target = pert_entry[target_key]
        pert_pred = pert_entry[prediction_key]
        for entry in file_results:
            loc = entry[location_key]
            unit_id = entry[unit_id_key]
            if pert_loc != loc:
                continue
            target = entry[target_key]
            pred = entry[prediction_key]
            if pert_target != target:
                continue
            all_perturbations.append((f"{unit_id}::{loc}", f"{pert_unit_id}::{pert_loc}"))
            if pert_pred == pred:
                continue
            success_perturbations.append((f"{unit_id}::{loc}", f"{pert_unit_id}::{pert_loc}"))
    
    return success_perturbations, all_perturbations

if __name__ == "__main__":
    __args = parse_args()
    file_path_key = __args.file_path_key
    unit_id_key = __args.unit_id_key
    location_key = __args.location_key
    target_key = __args.target_key
    prediction_key = __args.prediction_key
    name_feat = __args.name_feat
    filewise_pred_mapping_path = __args.filewise_pred_mapping_path
    detector_name = __args.detector_name

    for feature_name, feature_column_name in feature_name_dict.items():
        logging.info(feature_name)
        success_FR_perts = []
        all_FR_perts = []
        success_FP_perts = []
        all_FP_perts = []
        dataset_root = join(data_folder, feature_name)
        filewise_pred_mapping_filepath = join(dataset_root, "filewise_pred_mapping.json")
        with open(filewise_pred_mapping_filepath, "r") as rfi:
            filewise_pred_mapping = json.load(rfi)
        unperturbed_file_list_path = join(dataset_root, "unperturbed_file_list.json")
        with open(unperturbed_file_list_path, "r") as rfi:
            unperturbed_file_list = json.load(rfi)
        for filepath, file_results in filewise_pred_mapping.items():
            if filepath not in unperturbed_file_list:
                continue
            filepath_wo_ext, ext = splitext(filepath)
            file_preturbation_results = {key:value for key, value in filewise_pred_mapping.items() if len(key) > len(filepath) and filepath_wo_ext in key}
            
            for perturbed_filepath, perturbed_file_results in file_preturbation_results.items():
                perturbed_filepath_wo_ext, perturbed_ext = splitext(perturbed_filepath)
                perturbation_info = perturbed_filepath_wo_ext.replace(filepath_wo_ext, "").split("_")[1:]
                if "FR" in perturbation_info:
                    perturbation_response = get_FR_perturbation_response(file_results, perturbed_file_results, feature_name, perturbation_info)
                    success_FR_perts += perturbation_response[0]
                    all_FR_perts += perturbation_response[1]
                elif "FP" in perturbation_info:
                    perturbation_response = get_FP_perturbation_response(file_results, perturbed_file_results, feature_name, perturbation_info)
                    success_FP_perts += perturbation_response[0]
                    all_FP_perts += perturbation_response[1]
        FR_success_rate = (len(success_FR_perts) / len(all_FR_perts)) * 100 if  len(all_FR_perts) else 0
        FP_success_rate = (len(success_FP_perts) / len(all_FP_perts)) * 100 if  len(all_FP_perts) else 0
        feature_column_name_list.append(feature_column_name)
        FR_success_cnt_list.append(len(success_FR_perts))
        FR_all_cnt_list.append(len(all_FR_perts))
        FR_success_rate_list.append(FR_success_rate)
        FP_success_cnt_list.append(len(success_FP_perts))
        FP_all_cnt_list.append(len(all_FP_perts))
        FP_success_rate_list.append(FP_success_rate)
        logging.info(f"FP: {FP_success_rate}, FR: {FR_success_rate}")

    pd.DataFrame({
        "Feature Name": feature_column_name_list,
        "FP_succ_cnt": FP_success_cnt_list,
        "FP_all_cnt": FP_all_cnt_list,
        "FP Success Rate": FP_success_rate_list,
        "FR_succ_cnt": FR_success_cnt_list,
        "FR_all_cnt": FR_all_cnt_list,
        "FR Success Rate": FR_success_rate_list
    }).to_csv(f"{detector_name}_vf_rq3.csv", index=False)
