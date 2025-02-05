import os
import json
import logging
import pandas as pd

from argparse import ArgumentParser
from os.path import join, exists, isdir, isfile, basename, dirname, splitext
from tqdm import tqdm

data_folder = "replication"
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

spu_feat_list = ["tab", "symbolize", ]

spu_feats_dict = {"node_set": "Node Set", "edge_set": "Edge Set", "tab": "Code Formatting", "symbolize": "Identifier Name"}

FP_success_cnt_list = []
FP_all_cnt_list = []
FP_success_rate_list = []
feature_column_name_list = []

def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-u",
                            "--unit_id_key",
                            help="Key denoting the unique id for the unit of prediction",
                            default="unit_id",
                            type=str)
    arg_parser.add_argument("-l",
                            "--location_key",
                            help="Key denoting the location of the unit of prediction in source file",
                            default="loc",
                            type=str)
    arg_parser.add_argument("-t",
                            "--target_key",
                            help="Key denoting the ground truth label of the unit of prediction",
                            default="target",
                            type=str)
    arg_parser.add_argument("-p",
                            "--prediction_key",
                            help="Key denoting the prediction for the unit of prediction",
                            default="pred",
                            type=str)
    arg_parser.add_argument("-d",
                            "--detector_name",
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
            logging.FileHandler(join(LOG_DIR, "solution_evaluation_sf.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

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
    detector_name = __args.detector_name


    feature_column_name_list = []
    FP_success_cnt_list = []
    FP_all_cnt_list = []
    FP_success_rate_list = []
    rq2_results = []

    if detector_name in ["DeepWukong", "ReVeal"]:
        spu_feats_dict = {"node_set": "Node Set", "edge_set": "Edge Set"}
        for feature_name, feature_column_name in spu_feats_dict.items():
            pred_mapping_path = join(data_folder, feature_name, "pred_mapping.json")
            with open(pred_mapping_path, "r") as rfi:
                pred_mapping = json.load(rfi)
            
            total_FPPs = 0
            succ_FPPs = 0
            for xfg_path, xfg_info in pred_mapping.items():
                total_FPPs += 1
                if not xfg_info["pred_retained"]:
                    continue
                succ_FPPs += 1
            
            feature_column_name_list.append(feature_column_name)
            FP_success_cnt_list.append(succ_FPPs)
            FP_all_cnt_list.append(total_FPPs)
            succ_rate = (succ_FPPs / total_FPPs) * 100
            FP_success_rate_list.append(succ_rate)
            rq2_results.append(f"{succ_rate:.2f}")

        pd.DataFrame({
            "Feature Name": feature_column_name_list,
            "FPP_succ_cnt": FP_success_cnt_list,
            "FPP_all_cnt": FP_all_cnt_list,
            "FPP Success Rate": FP_success_rate_list,
            "rq2": rq2_results
        }).to_csv(f"{detector_name}_sf_rq2.csv", index=False)
    elif detector_name == "LineVul":
        spu_feats_dict = {"tab": "Code Formatting", "symbolize": "Identifier Name"}
        with open(join(data_folder, "SARD", "function_pred_mapping.json") , "r") as rfi:
            orig_function_pred_mapping = json.load(rfi)
         
        for feature_name, feature_column_name in spu_feats_dict.items():
            function_pred_mapping_filepath = join(data_folder, feature_name, "function_pred_mapping.json")
            with open(function_pred_mapping_filepath, "r") as rfi:
                pert_function_pred_mapping = json.load(rfi)
            
            total_FPPs = 0
            succ_FPPs = 0

            for function_key, results in pert_function_pred_mapping.items():
                total_FPPs += 1
                if results[prediction_key] != orig_function_pred_mapping[function_key][prediction_key]:
                    continue
                succ_FPPs += 1
            
            feature_column_name_list.append(feature_column_name)
            FP_success_cnt_list.append(succ_FPPs)
            FP_all_cnt_list.append(total_FPPs)
            succ_rate = (succ_FPPs / total_FPPs) * 100
            FP_success_rate_list.append(succ_rate)
            rq2_results.append(f"{succ_rate:.2f}")

        pd.DataFrame({
            "Feature Name": feature_column_name_list,
            "FPP_succ_cnt": FP_success_cnt_list,
            "FPP_all_cnt": FP_all_cnt_list,
            "FPP Success Rate": FP_success_rate_list,
            "rq2": rq2_results
        }).to_csv(f"{detector_name}_sf_rq2.csv", index=False)
    elif detector_name == "SySeVR":
        spu_feats_dict = {"tab": "Code Formatting", "symbolize": "Identifier Name"}
        with open(join(data_folder, "SARD", "pred_mapping.json"), "r") as rfi:
            orig_pred_mapping = json.load(rfi)
        
        trimmed_orig_pred_mapping = dict()
        for slice_key, results in tqdm(orig_pred_mapping.items(), total=len(orig_pred_mapping)):
            slice_parts = slice_key.split()
            trimmed_slice_key = f"{slice_parts[1]}::{slice_parts[3]}"
            trimmed_orig_pred_mapping[trimmed_slice_key] = results
        

        feature_column_name_list = []
        FP_success_cnt_list = []
        FP_all_cnt_list = []
        FP_success_rate_list = []
        rq2_results = []

        for feature_name, feature_column_name in spu_feats_dict.items():
            with open(join(data_folder, feature_name, "pred_mapping.json"), "r") as rfi:
                pert_pred_mapping = json.load(rfi)
            trimmed_pert_pred_mapping = dict()
            for slice_key, results in tqdm(pert_pred_mapping.items(), total=len(pert_pred_mapping)):
                slice_parts = slice_key.split()
                trimmed_slice_key = f"{slice_parts[1]}::{slice_parts[3]}"
                trimmed_pert_pred_mapping[trimmed_slice_key] = results
            
            total_FPPs = 0
            succ_FPPs = 0

            for slice_key, results in trimmed_pert_pred_mapping.items():
                if slice_key not in trimmed_orig_pred_mapping:
                    continue
                total_FPPs += 1
                if slice_key in trimmed_orig_pred_mapping and results["pred"] == trimmed_orig_pred_mapping[slice_key]["pred"]:
                    succ_FPPs += 1
            
            feature_column_name_list.append(feature_column_name)

            FP_success_cnt_list.append(succ_FPPs)
            FP_all_cnt_list.append(total_FPPs)
            succ_rate = (succ_FPPs / total_FPPs) * 100
            FP_success_rate_list.append(succ_rate)
            rq2_results.append(f"{succ_rate:.2f}")
        pd.DataFrame({
            "Feature Name": feature_column_name_list,
            "FPP_succ_cnt": FP_success_cnt_list,
            "FPP_all_cnt": FP_all_cnt_list,
            "FPP Success Rate": FP_success_rate_list,
            "rq2": rq2_results
        }).to_csv(f"{detector_name}_sf_rq2.csv", index=False)
