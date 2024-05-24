import functools
import os
import json
import logging

from multiprocessing import Manager, Pool, Queue, cpu_count
from os.path import join, exists, relpath, isdir
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

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "feature_detection.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def process_file_parallel(cpp_path, queue: Queue):
    nodes_dir = join(csv_path, cpp_path)
    CPG = build_CPG(nodes_dir, cpp_path)

    detection_algos = [incorr_calc_buff_size, buff_access_src_size, off_by_one, buff_overread, double_free, use_after_free, buff_underwrite, buff_underread]
    sensi_algos = [sensi_read, sensi_write]

    detection_results = []
    for algo in detection_algos:
        try:
            detection_results.append(algo(nodes_dir, CPG)[1:])
        except Exception as e:
            logging.error(cpp_path)

    Y = []
    if cpp_path in ground_truth:
        Y = ground_truth[cpp_path]
    for algo in sensi_algos:
        try:
            detection_results.append(algo(nodes_dir, CPG, Y)[1:])
        except Exception as e:
            logging.error(cpp_path)
    
    return {cpp_path: detection_results}


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

    all_cpp_paths_filepath = join(dataset_root, config.cpp_paths_filename)

    if not exists(all_cpp_paths_filepath):
        logging.info(f"{all_cpp_paths_filepath} not found. Retriving all source code files from {source_root_path}...")
        for root, dirs, files in os.walk(source_root_path, topdown=True):
            for file_name in files:
                rel_dir = relpath(root, source_root_path)
                rel_file = join(rel_dir, file_name)
                if not rel_file.endswith(".c") and not rel_file.endswith(".cpp") and not rel_file.endswith(".h"):
                    continue
                all_cpp_paths.append(rel_file)
        logging.info(f"Successfully retrieved {len(all_cpp_paths)} files. Writing all cpp_paths to {all_cpp_paths_filepath}...")
        with open(all_cpp_paths_filepath, "w") as wfi:
            json.dump(all_cpp_paths, wfi)
    else:
        logging.info(f"Retrieving cpp filepaths from {all_cpp_paths_filepath}...")
        with open(all_cpp_paths_filepath, "r") as rfi:
            all_cpp_paths = json.load(rfi)
        logging.info("Completed.")
    
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
    
    detection_result_dict = dict()
    logging.info(f"Converting data to JSON...")
    for entry in detection_result_list:
        for key, value in entry.items():
            detection_result_dict[key] = value
    
    detection_result_path = join(dataset_root, config.detection_result_filename)
    logging.info(f"Conversion completed. Writing detection results to {detection_result_path}...")
    with open(detection_result_path, "w") as wfi:
        json.dump(detection_result_dict, wfi, indent=2)
    logging.info("Completed.")