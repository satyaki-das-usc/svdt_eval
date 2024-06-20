from functools import reduce
from os.path import join, dirname, splitext, basename
from shutil import copyfile

from src.common_utils import copy_directory

def contains_any_substring(string, substrings):
    for substring in substrings:
        if substring in string:
            return True
    return False

def perturb_sensi_read(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, v, called_sensi_func = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)
    neutral_sensi_filepath = "neutral_sensi.h"
    dest_neutral_sensi_filepath = join(dst_cpp_dir, neutral_sensi_filepath)
    copyfile(neutral_sensi_filepath, dest_neutral_sensi_filepath)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    rm_sensi_call_dst_lines = [] + src_lines
    rm_sensi_call_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(func_name, f"neutral_{func_name}") for func_name in called_sensi_func], src_lines[v - 1])
    
    first_code_loc = int([node for node in joern_nodes if len(node["location"].strip()) > 0][0]["location"].split(":")[0].strip())
    last_include_line_num = first_code_loc
    while last_include_line_num >= 0:
        line_txt = src_lines[last_include_line_num]
        last_include_line_num -= 1
        if not line_txt.startswith("#include"):
            continue
        break
    include_txt = '#include "neutral_sensi.h"\n'
    last_include_line_num += 2

    rm_sensi_call_dst_lines = rm_sensi_call_dst_lines[:last_include_line_num] + [include_txt] + rm_sensi_call_dst_lines[last_include_line_num:]

    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_sensi_call_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    replace_w_sim_sensi_dst_lines = [] + src_lines
    if not contains_any_substring(src_lines[v - 1].strip(), ["getch", "getchar"]):
        return {cpp_path: {feat_name: perturbed_file_paths}}
    
    if "getch" in src_lines[v - 1]:
        replace_w_sim_sensi_dst_lines[v - 1] = src_lines[v - 1].replace("getch", "getchar")
    elif "getchar" in src_lines[v - 1]:
        replace_w_sim_sensi_dst_lines[v - 1] = src_lines[v - 1].replace("getchar", "getch")

    postfix = f"{v}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(replace_w_sim_sensi_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_sensi_write(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, v, called_sensi_func = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)
    neutral_sensi_filepath = "neutral_sensi.h"
    dest_neutral_sensi_filepath = join(dst_cpp_dir, neutral_sensi_filepath)
    copyfile(neutral_sensi_filepath, dest_neutral_sensi_filepath)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []


    rm_sensi_call_dst_lines = [] + src_lines
    rm_sensi_call_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(func_name, f"neutral_{func_name}") for func_name in called_sensi_func], src_lines[v - 1])
    
    first_code_loc = int([node for node in joern_nodes if len(node["location"].strip()) > 0][0]["location"].split(":")[0].strip())
    last_include_line_num = first_code_loc
    while last_include_line_num >= 0:
        line_txt = src_lines[last_include_line_num]
        last_include_line_num -= 1
        if not line_txt.startswith("#include"):
            continue
        break
    include_txt = '#include "neutral_sensi.h"\n'

    last_include_line_num += 2
    rm_sensi_call_dst_lines = rm_sensi_call_dst_lines[:last_include_line_num] + [include_txt] + rm_sensi_call_dst_lines[last_include_line_num:]
    
    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_sensi_call_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    replace_w_sim_sensi_dst_lines = [] + src_lines
    if not contains_any_substring(src_lines[v - 1].strip(), ["memcpy", "strncpy"]):
        return {cpp_path: {feat_name: perturbed_file_paths}}
    
    if "memcpy" in src_lines[v - 1]:
        replace_w_sim_sensi_dst_lines[v - 1] = src_lines[v - 1].replace("memcpy", "strncpy")
    elif "strncpy" in src_lines[v - 1]:
        replace_w_sim_sensi_dst_lines[v - 1] = src_lines[v - 1].replace("strncpy", "memcpy")
    postfix = f"{v}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(replace_w_sim_sensi_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass