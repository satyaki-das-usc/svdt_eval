from os.path import join, dirname, splitext, basename

from src.common_utils import copy_directory, match_leading_spaces

def generate_line_w_condition(line_txt, idx, literal):
    return f"if({idx} {'>=' if literal == 0 else '>'} {literal}) {{ {line_txt.strip()} }}\n"

def generate_line_w_wrong_condition(line_txt, idx, literal):
    return f"if({idx} {'<' if literal == 0 else '>='} {literal}) {{ {line_txt.strip()} }}\n"

def perturb_buff_underwrite(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, v, b, idx = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    cond_for_0_dst_lines = [] + src_lines
    cond_for_0_dst_lines[v - 1] = match_leading_spaces(generate_line_w_condition(src_lines[v - 1], idx, 0), src_lines[v - 1])
    postfix = f"{v}_FR_0"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(cond_for_0_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    cond_for_neg_1_dst_lines = [] + src_lines
    cond_for_neg_1_dst_lines[v - 1] = match_leading_spaces(generate_line_w_condition(src_lines[v - 1], idx, -1), src_lines[v - 1])
    postfix = f"{v}_FR_neg_1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(cond_for_neg_1_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    wrong_cond_for_0_dst_lines = [] + src_lines
    wrong_cond_for_0_dst_lines[v - 1] = match_leading_spaces(generate_line_w_wrong_condition(src_lines[v - 1], idx, 0), src_lines[v - 1])
    postfix = f"{v}_FP_0"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(wrong_cond_for_0_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    wrong_cond_for_neg_1_dst_lines = [] + src_lines
    wrong_cond_for_neg_1_dst_lines[v - 1] = match_leading_spaces(generate_line_w_wrong_condition(src_lines[v - 1], idx, -1), src_lines[v - 1])
    postfix = f"{v}_FP_neg_1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(wrong_cond_for_neg_1_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def perturb_buff_underread(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, v, b, idx = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    cond_for_0_dst_lines = [] + src_lines
    cond_for_0_dst_lines[v - 1] = match_leading_spaces(generate_line_w_condition(src_lines[v - 1], idx, 0), src_lines[v - 1])
    postfix = f"{v}_FR_0"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(cond_for_0_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    cond_for_neg_1_dst_lines = [] + src_lines
    cond_for_neg_1_dst_lines[v - 1] = match_leading_spaces(generate_line_w_condition(src_lines[v - 1], idx, -1), src_lines[v - 1])
    postfix = f"{v}_FR_neg_1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(cond_for_neg_1_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    wrong_cond_for_0_dst_lines = [] + src_lines
    wrong_cond_for_0_dst_lines[v - 1] = match_leading_spaces(generate_line_w_wrong_condition(src_lines[v - 1], idx, 0), src_lines[v - 1])
    postfix = f"{v}_FP_0"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(wrong_cond_for_0_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    wrong_cond_for_neg_1_dst_lines = [] + src_lines
    wrong_cond_for_neg_1_dst_lines[v - 1] = match_leading_spaces(generate_line_w_wrong_condition(src_lines[v - 1], idx, -1), src_lines[v - 1])
    postfix = f"{v}_FP_neg_1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(wrong_cond_for_neg_1_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass