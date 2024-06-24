from os.path import join, dirname, splitext, basename

from src.common_utils import copy_directory, replace_substring_with_spaces, match_leading_spaces

def perturb_double_free(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, b, x, u, v = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    rm_first_free_dst_lines = [] + src_lines
    line_txt_trimmed = src_lines[u - 1].splitlines()[0].replace(" ", "")
    commented_out_line_txt_trimmed = f"/* {line_txt_trimmed} */"
    rm_first_free_dst_lines[u - 1] = replace_substring_with_spaces(src_lines[u - 1], line_txt_trimmed, commented_out_line_txt_trimmed)

    postfix = f"{u}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_first_free_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    rm_second_free_dst_lines = [] + src_lines
    line_txt_trimmed = src_lines[v - 1].splitlines()[0].replace(" ", "")
    commented_out_line_txt_trimmed = f"/* {line_txt_trimmed} */"
    rm_second_free_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], line_txt_trimmed, commented_out_line_txt_trimmed)

    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_second_free_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    new_allocation_line = match_leading_spaces(src_lines[x - 1], src_lines[v - 1])
    
    alloc_between_frees_dst_lines = src_lines[:v - 1] + [new_allocation_line] + src_lines[v - 1:]
    postfix = f"{v}_FR_{v}+1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_between_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    alloc_after_frees_dst_lines = src_lines[:v] + [new_allocation_line] + src_lines[v:]
    postfix = f"{v}_FP_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_after_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    new_allocation_line = match_leading_spaces(src_lines[x - 1], src_lines[u - 1])
    alloc_before_frees_dst_lines = src_lines[:u - 1] + [new_allocation_line] + src_lines[u - 1:]
    postfix = f"{u}_FP_{v}+1"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_before_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

def requires_new_deallocation_line(new_deallocation_line, v_str_trimmed):
    if new_deallocation_line is None:
        return False
    if v_str_trimmed.startswith("return"):
        return False
    return True

def perturb_use_after_free(entry, nodes_dir, joern_nodes, dataset_root, source_root_path, cpp_path):
    feat_name, b, x, u, v = entry

    filename, extension = splitext(basename(cpp_path))

    src_cpp_file_path = join(source_root_path, cpp_path)
    dst_cpp_dir = dirname(join(dataset_root, feat_name, cpp_path))

    src_cpp_dir = dirname(src_cpp_file_path)
    copy_directory(src_cpp_dir, dst_cpp_dir)

    with open(src_cpp_file_path, "r") as rfi:
        src_lines = rfi.readlines()
    
    cpp_dir = dirname(cpp_path)
    perturbed_file_paths = []

    new_allocation_line = match_leading_spaces(src_lines[x - 1], src_lines[v - 1])
    free_buff_txt = f"free({b})"
    v_str_trimmed = src_lines[v - 1].replace(" ", "")
    new_deallocation_line = None
    if free_buff_txt not in v_str_trimmed:
        new_deallocation_line = match_leading_spaces(src_lines[u - 1], src_lines[v - 1])
    alloc_before_use_dst_lines = src_lines[:v-1] + [new_allocation_line, src_lines[v-1]]
    if requires_new_deallocation_line(new_deallocation_line, v_str_trimmed):
        alloc_before_use_dst_lines.append(new_deallocation_line)
    alloc_before_use_dst_lines += src_lines[v:]

    postfix = f"{v}_FR_{v}+1{'+1' if requires_new_deallocation_line(new_deallocation_line, v_str_trimmed) else '+0'}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_before_use_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    rm_use_dst_lines = [] + src_lines
    line_txt_trimmed = src_lines[v - 1].splitlines()[0].replace(" ", "")
    commented_out_line_txt_trimmed = f"/* {line_txt_trimmed} */"
    rm_use_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], line_txt_trimmed, commented_out_line_txt_trimmed)

    postfix = f"{v}_FR_{v}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_use_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    mv_free_after_use_dst_lines = src_lines[:u - 1] + src_lines[u:v]
    if requires_new_deallocation_line(new_deallocation_line, v_str_trimmed):
        mv_free_after_use_dst_lines.append(new_deallocation_line)
    mv_free_after_use_dst_lines += src_lines[v:]
    
    postfix = f"{u}_FR_{v}+-1{'+1' if requires_new_deallocation_line(new_deallocation_line, v_str_trimmed) else '+0'}"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(mv_free_after_use_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    alloc_after_use_dst_lines = src_lines[:v] + [new_allocation_line]
    alloc_after_use_dst_lines.append(match_leading_spaces(src_lines[u - 1], src_lines[v - 1]))
    alloc_after_use_dst_lines += src_lines[v:]

    postfix = f"{v}_FP_{v}+0+2"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_after_use_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass