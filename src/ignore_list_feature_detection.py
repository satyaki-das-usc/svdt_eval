import functools
import os
import json
import logging

from multiprocessing import Manager, Pool, Queue, cpu_count
from os.path import join, isdir
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm
from typing import List, cast

from src.common_utils import *
from src.cpg_rules.overflow_vulnerability_rules import incorr_calc_buff_size, buff_access_src_size, off_by_one, buff_overread
from src.cpg_rules.dealloc_vulnerability_rules import double_free, use_after_free
from src.cpg_rules.num_range_vulnerability_rules import buff_underwrite, buff_underread
from src.cpg_rules.sensi_api_vulnerability_rules import sensi_read, sensi_write

USE_CPU = cpu_count()

ground_truth = dict()
data_folder = ""
dataset_root = ""
source_root_path = ""
csv_path = ""
ignore_list_results_dir = "ignore_list_results"

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "ignore_list_feature_detection.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def process_file_parallel(cpp_path, queue: Queue):
    logging.info(f"Processing {cpp_path}...")
    results_dir = join(ignore_list_results_dir, cpp_path)
    results_filepath = join(results_dir, "results.json")
    if exists(results_filepath):
        with open(results_filepath, "r") as rfi:
            logging.info(f"{cpp_path} processing completed.")
            return {cpp_path: json.load(rfi)}
    try:
        detection_results = []
        if cpp_path in ["000/153/513/utils.c"]:
            return {cpp_path: detection_results}

        nodes_dir = join(csv_path, cpp_path)
        CPG = build_CPG(nodes_dir, cpp_path)

        detection_algos = [incorr_calc_buff_size, buff_access_src_size, off_by_one, buff_overread, double_free, use_after_free, buff_underwrite, buff_underread]
        sensi_algos = [sensi_read, sensi_write]

        for algo in detection_algos:
            detection_results.append(algo(nodes_dir, CPG)[1:])

        Y = []
        if cpp_path in ground_truth:
            Y = ground_truth[cpp_path]
        for algo in sensi_algos:
            detection_results.append(algo(nodes_dir, CPG, Y)[1:])
        
        if not exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        
        with open(results_filepath, "w") as wfi:
            json.dump(detection_results, wfi, indent=2)
        
        logging.info(f"{cpp_path} processing completed.")
        return {cpp_path: detection_results}
    except Exception as e:
        logging.error(cpp_path)
        raise e

if __name__ == "__main__":
    __args = parse_args()
    config = cast(DictConfig, OmegaConf.load(__args.config))
    repo_root = join("..", config.repo_root)
    data_folder = join(repo_root, config.data_folder)
    dataset_root = join(data_folder, config.dataset.name)
    init_log()
    
    source_root_path = join(dataset_root, config.source_root_folder)
    csv_path = join(dataset_root, config.csv_folder)

    ground_truth_path = join(dataset_root, config.ground_truth_filename)
    logging.info(f"Reading ground truth from {ground_truth_path}...")
    with open(ground_truth_path, "r") as rfi:
        ground_truth = json.load(rfi)
    logging.info("Completed.")

    all_cpp_paths = []

    all_cpp_paths_filepath = join(dataset_root, config.ignore_list_filename)
    with open(all_cpp_paths_filepath, "r") as rfi:
        all_cpp_paths = set(json.load(rfi))
    
    logging.info(f"Going over {len(all_cpp_paths)} files...")
    with Manager() as m:
        message_queue = m.Queue()  # type: ignore
        pool = Pool(USE_CPU)
        process_func = functools.partial(process_file_parallel, queue=message_queue)
        detection_result_list: List = [
            filename
            for filename in tqdm(
                pool.imap_unordered(process_func, all_cpp_paths),
                desc=f"Source files",
                total=len(all_cpp_paths),
            )
        ]

        message_queue.put("finished")
        pool.close()
        pool.join()

    detection_result_list = [result for result in detection_result_list if isinstance(result, dict)]
    
    detection_result_dict = dict()
    logging.info(f"Converting data to JSON...")
    for entry in detection_result_list:
        for key, value in entry.items():
            detection_result_dict[key] = value
    
    detection_result_path = join(dataset_root, config.ignore_list_detection_result_filename)
    logging.info(f"Conversion completed. Writing detection results to {detection_result_path}...")
    with open(detection_result_path, "w") as wfi:
        json.dump(detection_result_dict, wfi, indent=2)
    logging.info("Completed.")