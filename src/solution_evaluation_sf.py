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

spu_feat_list = ["tab", "symbolize", ]

spu_feats_dict = {"node_set": "Node Set", "edge_set": "Edge Set", "tab": "Code Formatting", "symbolize": "Identifier Name"}

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
                            default="pred",
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

    feature_column_name_list = []
    FP_success_cnt_list = []
    FP_all_cnt_list = []
    FP_success_rate_list = []
    rq2_results = []

    for feature_name, feature_column_name in spu_feats_dict.items():
        pred_mapping_path = f"data/{feature_name}/verbose_results/pred_mapping.json"
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
