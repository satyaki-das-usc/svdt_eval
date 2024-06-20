from functools import reduce
from os.path import join, dirname, splitext, basename

from src.common_utils import copy_directory

def perturb_sensi_read(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, v, called_sensi_func = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    rm_sensi_call_dst_lines = [] + src_lines
    rm_sensi_call_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(func_name, f"neutral_func{idx+1}") for idx, func_name in enumerate(called_sensi_func)], src_lines[v - 1])
    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_sensi_call_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    replace_w_sim_sensi_dst_lines = [] + src_lines
    sensi_read_replacements = {
        "getch": "getchar",
        "getchar": "getch",
        "fgets": "fgets",
        "gets": "gets",
        "fgetc": "fgetc"
    }
    replace_w_sim_sensi_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(funcname, sensi_read_replacements[funcname]) for funcname in called_sensi_func], src_lines[v - 1])
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

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []


    rm_sensi_call_dst_lines = [] + src_lines
    rm_sensi_call_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(func_name, f"neutral_func{idx+1}") for idx, func_name in enumerate(called_sensi_func)], src_lines[v - 1])
    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_sensi_call_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    replace_w_sim_sensi_dst_lines = [] + src_lines
    sensi_write_replacements = {
       "memcpy": "strncpy",
       "strncpy": "memcpy",
       "strcpy": "strcpy",
       "wcsncpy": "wcsncpy",
       "memset": "memset",
       "wmemset": "wmemset"
    }
    replace_w_sim_sensi_dst_lines[v - 1] = reduce(lambda txt, rep: txt.replace(*rep), [(funcname, sensi_write_replacements[funcname]) for funcname in called_sensi_func], src_lines[v - 1])
    postfix = f"{v}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(replace_w_sim_sensi_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass