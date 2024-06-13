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

    postfix = f"{u}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_first_free_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    rm_second_free_dst_lines = [] + src_lines
    line_txt_trimmed = src_lines[v - 1].splitlines()[0].replace(" ", "")
    commented_out_line_txt_trimmed = f"/* {line_txt_trimmed} */"
    rm_second_free_dst_lines[v - 1] = replace_substring_with_spaces(src_lines[v - 1], line_txt_trimmed, commented_out_line_txt_trimmed)

    postfix = f"{v}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(rm_second_free_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    new_allocation_line = match_leading_spaces(src_lines[x - 1], src_lines[v - 1])
    
    alloc_between_frees_dst_lines = src_lines[:v - 1] + [new_allocation_line] + src_lines[v - 1:]
    postfix = f"{v + 1}_FR"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_between_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))
    
    alloc_after_frees_dst_lines = src_lines[:v] + [new_allocation_line] + src_lines[v:]
    postfix = f"{v}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_after_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    new_allocation_line = match_leading_spaces(src_lines[x - 1], src_lines[u - 1])
    alloc_before_frees_dst_lines = src_lines[:u - 1] + [new_allocation_line] + src_lines[u - 1:]
    postfix = f"{u + 1}_FP"
    dst_filename = f"{filename}_{postfix}{extension}"
    dst_cpp_file_path = join(dst_cpp_dir, dst_filename)
    with open(dst_cpp_file_path, "w") as wfi:
        wfi.writelines(alloc_before_frees_dst_lines)
    perturbed_file_paths.append(join(cpp_dir, dst_filename))

    return {cpp_path: {feat_name: perturbed_file_paths}}

if __name__ == "__main__":
    pass