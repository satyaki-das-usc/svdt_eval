import os
import json

from os.path import isdir, exists, dirname, join

from tqdm import  tqdm

if __name__ == "__main__":
    with open("data/SARD/file_function.json", "r") as rfi:
        file_function_map = json.load(rfi)

    with open("data/SARD/ground_truth.json", "r") as rfi:
        ground_truth = json.load(rfi)

    perturbed_ground_truth = dict()

    node_set_path = "data/node_set/source-code"
    if not isdir(node_set_path):
        os.makedirs(node_set_path, exist_ok=True)
    edge_set_path = "data/edge_set/source-code"
    if not isdir(edge_set_path):
        os.makedirs(edge_set_path, exist_ok=True)

    for file_path, functions in tqdm(file_function_map.items(), total=len(file_function_map)):
        with open(file_path, "r") as rfi:
            src_lines = rfi.readlines()
        node_set_dst_lines = [] + src_lines
        edge_set_dst_lines = [] + src_lines
        cpp_path = file_path.split("source-code/")[-1]
        vul_lines = []
        if cpp_path in ground_truth:
            vul_lines = ground_truth[cpp_path]
        cpp_dir = dirname(cpp_path)
        node_set_filedir = join(node_set_path, cpp_dir)
        if not isdir(node_set_filedir):
            os.makedirs(node_set_filedir, exist_ok=True)
        edge_set_filedir = join(edge_set_path, cpp_dir)
        if not isdir(edge_set_filedir):
            os.makedirs(edge_set_filedir, exist_ok=True)
        for idx, func in enumerate(functions):
            func_start_line = func["line_nums"][0]
            node_set_dst_lines.insert(func_start_line + idx + 1, f"    printf("");\n")
            edge_set_dst_lines.insert(func_start_line + idx + 1, f"    if(0 != 1) return;\n")
            vul_lines = [ln if ln <= func_start_line else ln + 1 for ln in vul_lines]
        
        perturbed_ground_truth[cpp_path] = vul_lines
        
    node_set_ground_truth_path = join(node_set_path, "ground_truth.json")
    with open(node_set_ground_truth_path, "w") as wfi:
        json.dump(perturbed_ground_truth, wfi, indent=2)
    edge_set_ground_truth_path = join(edge_set_path, "ground_truth.json")
    with open(edge_set_ground_truth_path, "w") as wfi:
        json.dump(perturbed_ground_truth, wfi, indent=2)