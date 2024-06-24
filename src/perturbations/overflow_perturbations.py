from os.path import join, dirname, splitext, basename

from src.common_utils import copy_directory, replace_substring_with_spaces, create_min_check
from src.cpg_query import mu, get_buffer_write_byte_count_str, get_buffer_length_str, get_numeric_part, get_line_nodes, get_len_func_start_idx

def perturb_incorr_calc_buff_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, d, u, v = entry
    
    n_str = get_buffer_write_byte_count_str(joern_nodes, v)
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
    both_equal_to_n_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], len_d_str_trimmed, n_str_trimmed)
    
    postfix = f"{u}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    both_equal_to_len_d_dst_lines = [] + src_lines
    both_equal_to_len_d_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], n_str_trimmed, len_d_str_trimmed)

    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    lower_len_d_dst_lines = [] + src_lines
    lower_len_d_str = f"{len_d_str_trimmed} - 1"
    lower_len_d_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], len_d_str_trimmed, lower_len_d_str)
    
    postfix = f"{u}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(lower_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    higher_n_dst_lines = [] + src_lines
    higher_n_str = f"{n_str_trimmed} + 1"
    higher_n_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], n_str_trimmed, higher_n_str)

    postfix = f"{v}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(higher_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_buff_access_src_size(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, d, s, u, v, len_s_line = entry
    
    n_str = get_buffer_write_byte_count_str(joern_nodes, v)
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

    postfix = f"{v}_{len_s_line}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(src_len_n_inc_by_one_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    both_equal_to_n_dst_lines = [] + src_lines
    both_equal_to_n_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u-1], len_d_str_trimmed, n_str_trimmed)
    
    postfix = f"{u}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    both_equal_to_len_d_dst_lines = [] + src_lines
    both_equal_to_len_d_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], n_str_trimmed, len_d_str_trimmed)

    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_len_d_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_off_by_one(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, s, u, v = entry

    n_str = get_buffer_write_byte_count_str(joern_nodes, v)
    n_str_trimmed = n_str.replace(" ", "")
    n_numeric = get_numeric_part(n_str_trimmed)
    n_numeric_wo_plus_one = replace_substring_with_spaces(n_numeric, "+1", "").lstrip("(").rstrip(")")
    
    len_s_str = get_buffer_length_str(joern_nodes, u, mu(nodes_dir, "type", u))
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

    larger_src_dst_lines = [] + src_lines
    len_s_numeric_plus_one = f"{len_s_numeric}+1"
    larger_src_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], len_s_numeric, len_s_numeric_plus_one)
    
    postfix = f"{u}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(larger_src_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    min_check_dst_lines = [] + src_lines
    line_nodes = get_line_nodes(joern_nodes, v)
    arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]
    len_func_start_idx = get_len_func_start_idx(line_nodes)
    src_len_func_call = replace_substring_with_spaces(line_nodes[len_func_start_idx - 1]["code"], " ", "")
    src_len_func_call_plus_one = f"{src_len_func_call}+1"
    dst_len_func_call = src_len_func_call.replace(s, arg_nodes[0]["code"].strip())
    min_check_replacement = create_min_check(src_len_func_call, dst_len_func_call)
    if src_len_func_call_plus_one in n_str_trimmed:
        min_check_dst_lines[v-1] = replace_substring_with_spaces(src_lines[v-1], src_len_func_call_plus_one, min_check_replacement)
    else:
        min_check_dst_lines[v-1] = replace_substring_with_spaces(src_lines[v-1], src_len_func_call, min_check_replacement)
    
    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(min_check_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_buff_overread(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, s, u, v, n_str = entry

    n_str_trimmed = n_str.replace(" ", "")
    
    len_s_str = get_buffer_length_str(joern_nodes, u, mu(nodes_dir, "type", u))
    len_s_str_trimmed = len_s_str.replace(" ", "")

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    both_equal_to_n_dst_lines = [] + src_lines
    both_equal_to_n_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], len_s_str_trimmed, n_str_trimmed)
    
    postfix = f"{u}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    both_equal_to_len_s_dst_lines = [] + src_lines
    n_str_v = get_buffer_write_byte_count_str(joern_nodes, v)
    n_str_v_trimmed = n_str_v.replace(" ", "")
    both_equal_to_len_s_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], n_str_v_trimmed, len_s_str_trimmed)

    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(both_equal_to_len_s_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    lower_len_s_dst_lines = [] + src_lines
    lower_len_s_str = f"{len_s_str_trimmed} - 1"
    lower_len_s_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], len_s_str_trimmed, lower_len_s_str)
    
    postfix = f"{u}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(lower_len_s_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    higher_n_dst_lines = [] + src_lines
    higher_n_str = f"{n_str_v_trimmed} + 1"
    higher_n_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], n_str_v_trimmed, higher_n_str)

    postfix = f"{v}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(higher_n_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass