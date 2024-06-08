from os.path import join, dirname, splitext, basename

from src.common_utils import copy_directory
from src.cpg_query import mu, get_concrete_buffer_write_byte_count_str, get_buffer_length_str, get_numeric_part

def perturb_incorr_calc_buff_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, d, u, v = entry
    n_str = get_concrete_buffer_write_byte_count_str(joern_nodes, v)
    n_str_trimmed = n_str.replace(" ", "")
    len_d_str = get_buffer_length_str(joern_nodes, u, mu(nodes_dir, "type", u))
    len_d_str_trimmed = len_d_str.replace(" ", "")

    src_cpp_file_path = join(source_root_path, cpp_path)

    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    filename, extension = splitext(basename(cpp_path))
    
    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    both_equal_to_n_dst_lines = [] + src_lines
    if len_d_str in src_lines[u-1]:
        both_equal_to_n_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str, n_str_trimmed)
    if len_d_str_trimmed in src_lines[u-1]:
        both_equal_to_n_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str_trimmed, n_str_trimmed)
    
    postfix = f"{u}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    both_equal_to_len_d_dst_lines = [] + src_lines
    if n_str in src_lines[v - 1]:
        both_equal_to_len_d_dst_lines[v - 1] = src_lines[v - 1].replace(n_str, len_d_str_trimmed)
    if n_str_trimmed in src_lines[v - 1]:
        both_equal_to_len_d_dst_lines[v - 1] = src_lines[v - 1].replace(n_str_trimmed, len_d_str_trimmed)

    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    lower_len_d_dst_lines = [] + src_lines
    if len_d_str in src_lines[u-1]:
        lower_n_str = f"{len_d_str} - 1"
        lower_len_d_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str, lower_n_str)
    if len_d_str_trimmed in src_lines[u-1]:
        lower_n_str = f"{len_d_str_trimmed} - 1"
        lower_len_d_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str_trimmed, lower_n_str)
    
    postfix = f"{u}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(lower_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    higher_n_dst_lines = [] + src_lines
    if n_str in src_lines[v - 1]:
        higher_n_str = f"{n_str} + 1"
        higher_n_dst_lines[v - 1] = src_lines[v - 1].replace(n_str, higher_n_str)
    if n_str_trimmed in src_lines[v - 1]:
        higher_n_str = f"{n_str_trimmed} + 1"
        higher_n_dst_lines[v - 1] = src_lines[v - 1].replace(n_str_trimmed, higher_n_str)

    postfix = f"{v}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(higher_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_buff_access_src_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, d, s, u, v, len_s_line = entry
    
    n_str = get_concrete_buffer_write_byte_count_str(joern_nodes, v)
    n_str_trimmed = n_str.replace(" ", "")
    n_numeric = get_numeric_part(n_str_trimmed)
    
    len_d_str = get_buffer_length_str(joern_nodes, u, mu(nodes_dir, "type", u))
    len_d_str_trimmed = len_d_str.replace(" ", "")
    len_d_numeric = get_numeric_part(len_d_str_trimmed)
    
    len_s_str = get_buffer_length_str(joern_nodes, len_s_line, mu(nodes_dir, "type", len_s_line))
    len_s_str_trimmed = len_s_str.replace(" ", "")
    len_s_numeric = get_numeric_part(len_s_str_trimmed)

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []
    
    src_len_n_inc_by_one_dst_lines = [] + src_lines
    perturbation_replacement = f"({len_s_numeric} + 1)"
    src_len_n_inc_by_one_dst_lines[v - 1] = src_lines[v - 1].replace(n_numeric, perturbation_replacement)
    src_len_n_inc_by_one_dst_lines[len_s_line - 1] = src_lines[len_s_line - 1].replace(n_numeric, perturbation_replacement)

    postfix = f"{v}_{len_s_line}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(src_len_n_inc_by_one_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    both_equal_to_n_dst_lines = [] + src_lines
    if len_d_str in src_lines[u-1]:
        both_equal_to_n_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str, n_str_trimmed)
    if len_d_str_trimmed in src_lines[u-1]:
        both_equal_to_n_dst_lines[u - 1] = src_lines[u-1].replace(len_d_str_trimmed, n_str_trimmed)
    
    postfix = f"{u}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    both_equal_to_len_d_dst_lines = [] + src_lines
    if n_str in src_lines[v - 1]:
        both_equal_to_len_d_dst_lines[v - 1] = src_lines[v - 1].replace(n_str, len_d_str_trimmed)
    if n_str_trimmed in src_lines[v - 1]:
        both_equal_to_len_d_dst_lines[v - 1] = src_lines[v - 1].replace(n_str_trimmed, len_d_str_trimmed)

    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass