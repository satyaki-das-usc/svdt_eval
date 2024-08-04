import functools
import json
import logging
import os

import pandas as pd

from argparse import ArgumentParser
# from src.preprocess.symbolizer import clean_gadget
from multiprocessing import Manager, Pool, Queue, cpu_count
from os.path import isdir, join, exists
from typing import List, cast

from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src.data_transfer.clean_utils import replace_leading_spaces_with_tabs, get_delabeled_processed_func, clean_gadget

USE_CPU = cpu_count()

data_folder = ""
dataset_root = ""
source_root_path = ""

cleaning_method = ""
function_metadata = dict()

def init_log():
    LOG_DIR = join(dataset_root, "logs")
    if not isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    logging.basicConfig(
        handlers=[
            logging.FileHandler(join(LOG_DIR, "generate_dataset_for_transfer.log")),
            logging.StreamHandler()
        ],
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info("=========New session=========")
    logging.info(f"Logging dir: {LOG_DIR}")

def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c",
                            "--config",
                            help="Path to YAML configuration file",
                            default="configs/dwk.yaml",
                            type=str)
    arg_parser.add_argument("--dataset-name", type=str, default=None)
    
    args = arg_parser.parse_args()

    return args

def generate_entry_for_file_parallel(cpp_path, queue: Queue):
    SRC_PATH = join(source_root_path, cpp_path)

    with open(SRC_PATH, "r") as rfi:
        src_lines = rfi.readlines()

    functions = function_metadata[cpp_path]

    processed_functions = []

    for func in functions:
        label_text = "good" if func["target"] == 0 else "bad"
        line_nums = sorted(set(list(range(func["start_line"], func["end_line"] + 1))))
        raw_funclines = src_lines[func["start_line"] - 1: func["end_line"]]
        raw_func = "".join(raw_funclines)
        processed_func = "" + raw_func
        if cleaning_method == "tab":
            processed_func = replace_leading_spaces_with_tabs(raw_funclines)
        if cleaning_method == "delabel":
            processed_func = get_delabeled_processed_func(raw_funclines, label_text)
        if cleaning_method == "symbolize":
            processed_func = clean_gadget(raw_funclines)
        processed_functions.append({
        "file_name": cpp_path,
        "line_nums": line_nums,
        "raw_func": raw_func,
        "func": processed_func,
        "target": func["target"],
        "commit_id": "",
        "project": ""
        })

    return processed_functions

if __name__ == "__main__":
    __args = parse_args()
    config = cast(DictConfig, OmegaConf.load(__args.config))
    data_folder = config.data_folder
    if __args.dataset_name is not None:
        config.dataset.name = __args.dataset_name
    if config.dataset.name == "SARD":
        dataset_root = data_folder
    else:
        dataset_root = join(data_folder, config.dataset.name)
    init_log()
    
    source_root_path = join(dataset_root, config.source_root_folder)
    cleaning_method = config.cleaning_method

    function_metadata_path = join(dataset_root, config.function_metadata_filename)

    logging.info(f"Reading function metadata from {function_metadata_path}...")
    with open(function_metadata_path, "r") as rfi:
        function_metadata = json.load(rfi)
    logging.info(f"Completed.")
    
    all_filepaths = list(function_metadata.keys())
    cnt = len(all_filepaths)

    logging.info(f"Going over {cnt} files...")
    with Manager() as m:
        message_queue = m.Queue()  # type: ignore
        pool = Pool(USE_CPU)
        process_func = functools.partial(generate_entry_for_file_parallel, queue=message_queue)
        file_entries: List = [
            filename
            for filename in tqdm(
                pool.imap_unordered(process_func, all_filepaths),
                desc=f"Files",
                total=cnt,
            )
        ]

        message_queue.put("finished")
        pool.close()
        pool.join()

    flattened_file_entries = [x for entries in file_entries for x in entries]

    clean_dir = join(dataset_root, cleaning_method)
    if not exists(clean_dir):
        os.makedirs(clean_dir, exist_ok=True)
    dataset_filepath = join(clean_dir, config.dataset_filename)
    logging.info(f"Completed. Writing dataset to {dataset_filepath}...")
    with open(dataset_filepath, "w") as wfi:
        json.dump(flattened_file_entries, wfi)
    logging.info(f"Writing Completed")


    logging.info(f"Generating data for bigvul...")
    processed_func_list = [entry["raw_func"] for entry in flattened_file_entries]
    target_list = [entry["target"] for entry in flattened_file_entries]
    file_name_list = [entry["file_name"] for entry in flattened_file_entries]
    line_nums_list = [entry["line_nums"] for entry in flattened_file_entries]
    flaw_line_list = ["" for entry in flattened_file_entries]
    flaw_line_index_list = ["" for entry in flattened_file_entries]

    clean_dir = join(dataset_root, "raw_func")
    if not exists(clean_dir):
        os.makedirs(clean_dir, exist_ok=True)
    bigvul_dataset_filepath = join(clean_dir, config.bigvul_dataset_filename)
    logging.info(f"Completed. Writing dataset to {bigvul_dataset_filepath}...")
    pd.DataFrame({
        "processed_func": processed_func_list,
        "target": target_list,
        "file_name": file_name_list,
        "line_nums": line_nums_list,
        "flaw_line": flaw_line_list,
        "flaw_line_index": flaw_line_index_list
    }).to_csv(bigvul_dataset_filepath, index=False)
    logging.info(f"Writing Completed")