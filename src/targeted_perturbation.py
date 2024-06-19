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
from src.perturbations.overflow_perturbations import perturb_incorr_calc_buff_size, perturb_buff_access_src_size, perturb_off_by_one, perturb_buff_overread
from src.perturbations.dealloc_perturbations import perturb_double_free, perturb_use_after_free
from src.perturbations.num_range_perturbations import perturb_buff_underwrite, perturb_buff_underread
from src.perturbations.sensi_api_perturbations import perturb_sensi_read, perturb_sensi_write

USE_CPU = cpu_count()

ground_truth = dict()
all_detection_results = dict()
data_folder = ""
dataset_root = ""
source_root_path = ""
csv_path = ""
perturbation_results_dir = "perturbation_results"

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "targeted_perturbation.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def process_file_parallel(cpp_path, queue: Queue):
    results_dir = join(perturbation_results_dir, cpp_path)
    results_filepath = join(results_dir, "perturbation_results.json")
    if exists(results_filepath):
        with open(results_filepath, "r") as rfi:
            return {cpp_path: json.load(rfi)}
    
    if cpp_path not in all_detection_results:
        return {cpp_path: None}
    detection_results = all_detection_results[cpp_path]

    nodes_dir = join(csv_path, cpp_path)
    nodes_path = join(nodes_dir, "nodes.csv")
    joern_nodes = read_csv(nodes_path)

    perturbation_results = []

    for result in detection_results:
        if len(result) == 0:
            continue
        for entry in result:
            if entry[0] == "incorr_calc_buff_size":
                perturbation_results.append(perturb_incorr_calc_buff_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "buff_access_src_size":
                perturbation_results.append(perturb_buff_access_src_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "off_by_one":
                perturbation_results.append(perturb_off_by_one(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "buff_overread":
                perturbation_results.append(perturb_buff_overread(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "double_free":
                perturbation_results.append(perturb_double_free(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "use_after_free":
                perturbation_results.append(perturb_use_after_free(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "buff_underwrite":
                perturbation_results.append(perturb_buff_underwrite(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "buff_underread":
                perturbation_results.append(perturb_buff_underread(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "sensi_read":
                perturbation_results.append(perturb_sensi_read(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
            elif entry[0] == "sensi_write":
                perturbation_results.append(perturb_sensi_write(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path)[cpp_path])
    
    if not exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)
    with open(results_filepath, "w") as wfi:
        json.dump(perturbation_results, wfi, indent=2)
    
    return {cpp_path: perturbation_results}

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

    detection_result_path = join(dataset_root, config.detection_result_filename)
    logging.info(f"Reading detection results from {detection_result_path}...")
    with open(detection_result_path, "r") as rfi:
        all_detection_results = json.load(rfi)
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
    
    ignore_list_filepath = join(dataset_root, config.ignore_list_filename)

    with open(ignore_list_filepath, "r") as rfi:
        ignore_list = set(json.load(rfi))
    
    all_cpp_paths = list(set(all_cpp_paths).difference(ignore_list))

    logging.info(f"Going over {len(all_cpp_paths)} files...")
    
    
    with Manager() as m:
        message_queue = m.Queue()  # type: ignore
        pool = Pool(USE_CPU)
        process_func = functools.partial(process_file_parallel, queue=message_queue)
        perturbation_result_list: List = [
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
    
    perturbation_result_dict = dict()
    logging.info(f"Converting data to JSON...")
    for entry in perturbation_result_list:
        for key, value in entry.items():
            perturbation_result_dict[key] = value
    
    perturbation_result_path = join(dataset_root, config.perturbation_result_filename)
    logging.info(f"Conversion completed. Writing perturbation results to {perturbation_result_path}...")
    with open(perturbation_result_path, "w") as wfi:
        json.dump(perturbation_result_dict, wfi, indent=2)
    logging.info("Completed.")