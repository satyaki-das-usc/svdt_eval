import re

from os.path import join

from src.common_utils import read_csv

def get_incoming_dd_edges_for_var(CPG, v, var):
    in_data_var = set()
    for edge in CPG.in_edges(v):
        u = edge[0]
        edge_data = CPG.get_edge_data(u, v)
        if edge_data["label"] != "REACHES":
            continue
        edge_var = edge_data["var"]
        if edge_var != var:
            continue
        in_data_var.add(u)
    
    return in_data_var

def get_incoming_cd_edges(CPG, v):
    in_ctrl_v = set()
    for edge in CPG.in_edges(v):
        u = edge[0]
        edge_data = CPG.get_edge_data(u, v)
        if edge_data["label"] != "CONTROLS":
            continue
        in_ctrl_v.add(u)
    
    return in_ctrl_v

def get_start_node_idx(joern_nodes, line_num):
    for idx, node in enumerate(joern_nodes):
        if len(node["location"]) == 0:
            continue
        loc = int(node["location"].split(":")[0])
        if line_num != loc:
            continue
        return idx
    return -1

def get_end_node_idx(joern_nodes, start_idx):
    for idx, node in enumerate(joern_nodes[start_idx + 1:]):
        if len(node["location"]) == 0:
            continue
        if node["isCFGNode"] != "True":
            continue
        return start_idx + 1 + idx
    return -1

def get_line_nodes(joern_nodes, line_num):
    start_idx = get_start_node_idx(joern_nodes, line_num)
    end_idx = get_end_node_idx(joern_nodes, start_idx)

    if end_idx < 0:
        return joern_nodes[start_idx:]
    
    return joern_nodes[start_idx: end_idx]

def is_buffer_write_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    if len([node for node in line_nodes if node["type"] == "CallExpression"]) == 0:
        return False
    return len([node for node in line_nodes if node["type"] == "Callee" and node["code"].strip() == "memcpy"]) > 0

def is_buffer_allocation_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    if len([node for node in line_nodes if node["type"] == "CallExpression"]) == 0:
        return False
    return len([node for node in line_nodes if node["type"] == "Callee" and node["code"].strip() == "malloc"]) > 0

def is_arr_decl(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    id_decl_nodes = [node for node in line_nodes if node["type"] == "IdentifierDeclType"]
    if len(id_decl_nodes) == 0:
        return False
    
    for node in id_decl_nodes:
        if "[" not in node["code"]:
            continue
        if "]" not in node["code"]:
            continue
        return True
    
    return False

def is_arr_index_write_operation(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arr_indexing_nodes = [node for node in line_nodes if node["type"] == "ArrayIndexing"]
    if len(arr_indexing_nodes) == 0:
        return False
    arr_indexing_str = arr_indexing_nodes[0]["code"].strip().replace(" ", "")
    asgnmt_expr_nodes = [node for node in line_nodes if node["type"] == "AssignmentExpression"]

    for node in asgnmt_expr_nodes:
        asgnmt_operator = node["operator"].strip()
        asgnmt_code_str = node["code"].strip()
        asgnmt_operand1, asgnmt_operand2 = [operand.replace(" ", "").strip() for operand in asgnmt_code_str.split(asgnmt_operator, maxsplit=1)]
        if asgnmt_operand1 != arr_indexing_str:
            continue
        return True
    
    return False

def is_arr_index_read_operation(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arr_indexing_nodes = [node for node in line_nodes if node["type"] == "ArrayIndexing"]
    if len(arr_indexing_nodes) == 0:
        return False
    arr_indexing_str = arr_indexing_nodes[0]["code"].strip().replace(" ", "")
    asgnmt_expr_nodes = [node for node in line_nodes if node["type"] == "AssignmentExpression"]
    
    for node in asgnmt_expr_nodes:
        asgnmt_operator = node["operator"].strip()
        asgnmt_code_str = node["code"].strip()
        asgnmt_operand1, asgnmt_operand2 = [operand.replace(" ", "").strip() for operand in asgnmt_code_str.split(asgnmt_operator, maxsplit=1)]
        if asgnmt_operand1 != arr_indexing_str:
            continue
        return False
    
    return True

def is_buffer_copy_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    if len([node for node in line_nodes if node["type"] == "CallExpression"]) == 0:
        return False
    return len([node for node in line_nodes if node["type"] == "Callee" and node["code"].strip() == "strncpy"]) > 0

def is_buffer_deallocation_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    if len([node for node in line_nodes if node["type"] == "CallExpression"]) == 0:
        return False
    return len([node for node in line_nodes if node["type"] == "Callee" and node["code"].strip() == "free"]) > 0

def is_relational_expression(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)

    return len([node for node in line_nodes if node["type"] == "RelationalExpression"]) > 0

def can_follow(CPG, u, v):
    if CPG.has_edge(v, u) and CPG.get_edge_data(v, u)["label"] == "POST_DOM":
        return True
    u_ctrl_edges = [edge for edge in CPG.in_edges(u) if CPG.get_edge_data(edge[0], edge[1])["label"] == "CONTROLS"]
    v_ctrl_edges = [edge for edge in CPG.in_edges(v) if CPG.get_edge_data(edge[0], edge[1])["label"] == "CONTROLS"]
    for x in u_ctrl_edges:
        for y in v_ctrl_edges:
            if CPG.has_edge(y[0], x[0]) and CPG.get_edge_data(y[0], x[0])["label"] == "POST_DOM":
                return True
    return False

def is_sensi_read_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    callee_nodes = [node for node in line_nodes if node["type"] == "Callee"]

    sensi_read_apis = ["getch", "fgets", "gets", "getchar", "fgetc"]
    for node in callee_nodes:
        callee_func = node["code"].strip()
        if callee_func not in sensi_read_apis:
            continue
        return True
    
    return False

def is_sensi_write_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    callee_nodes = [node for node in line_nodes if node["type"] == "Callee"]

    sensi_write_apis = ["memcpy", "strncpy", "strcpy", "wcsncpy", "memset", "wmemset"]
    for node in callee_nodes:
        callee_func = node["code"].strip()
        if callee_func not in sensi_write_apis:
            continue
        return True
    
    return False

def get_called_sensi_funcs(joern_nodes, v, key):
    line_nodes = get_line_nodes(joern_nodes, v)
    callee_nodes = [node for node in line_nodes if node["type"] == "Callee"]

    sensi_apis = []

    if key == "sensi_read_callee":
        sensi_apis = ["getch", "fgets", "gets", "getchar", "fgetc"]
    if key == "sensi_write_callee":
        sensi_apis = ["memcpy", "strncpy", "strcpy", "wcsncpy", "memset", "wmemset"]
    
    called_sensi_funcs = set()
    for node in callee_nodes:
        callee_func = node["code"].strip()
        if callee_func not in sensi_apis:
            continue
        called_sensi_funcs.add(callee_func)
    
    return list(called_sensi_funcs)

def get_node_type(joern_nodes, v):
    if is_buffer_write_function_call(joern_nodes, v):
        return "WF"
    elif is_buffer_allocation_function_call(joern_nodes, v):
        return "AF"
    elif is_arr_decl(joern_nodes, v):
        return "AD"
    elif is_buffer_copy_function_call(joern_nodes, v):
        return "CF"
    elif is_buffer_deallocation_function_call(joern_nodes, v):
        return "DF"
    elif is_arr_index_write_operation(joern_nodes, v):
        return "AIW"
    elif is_arr_index_read_operation(joern_nodes, v):
        return "AIR"
    elif is_relational_expression(joern_nodes, v):
        return "RE"
    elif is_sensi_read_function_call(joern_nodes, v):
        return "SRF"
    elif is_sensi_write_function_call(joern_nodes, v):
        return "SWF"
    return "UNK"

def get_buffer_write_dest(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]

    assert len(arg_nodes) == 3, f"ERROR: Buffer write with {len(arg_nodes)} arguments"

    return arg_nodes[0]["code"].strip()

def get_buffer_write_src(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]

    assert len(arg_nodes) == 3, f"ERROR: Buffer write with {len(arg_nodes)} arguments"

    return arg_nodes[1]["code"].strip()

def can_be_evaluated(math_expression):
    valid_pattern = re.compile(r'^[\d\+\-\*/\(\)\.\s]+$')
    
    if not valid_pattern.match(math_expression):
        return False
    
    try:
        result = eval(math_expression, {"__builtins__": None}, {})
    except:
        return False
    
    return True

def evaluate_size(size_str):
    expression = f"{size_str}".replace(" ", "").replace("]", "")
    replacements = {
        "sizeof(char)": "1",
        "sizeof(unsignedchar)": "1",
        "sizeof(signedchar)": "1",
        "sizeof(int)": "4",
        "sizeof(unsignedint)": "4",
        "sizeof(short)": "2",
        "sizeof(unsignedshort)": "2",
        "sizeof(long)": "8",
        "sizeof(unsignedlong)": "8",
        "sizeof(int64_t)": "8",
        "sizeof(twoIntsStruct)": "8",
        "char[": "1*",
        "unsignedchar[": "1*",
        "signedchar[": "1*",
        "int[": "4*",
        "unsignedint[": "4*",
        "short[": "2*",
        "unsignedshort[": "2*",
        "long[": "8*",
        "unsignedlong[": "8*",
        "int64_t[": "8*",
        "twoIntsStruct[": "8*"
    }
    for key, value in replacements.items():
        expression = expression.replace(key, value)

    if not can_be_evaluated(expression):
        return -2147483648
    return eval(expression)

def get_buffer_write_byte_count(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]

    assert len(arg_nodes) == 3, f"ERROR: Buffer write with {len(arg_nodes)} arguments"

    return evaluate_size(arg_nodes[2]["code"].strip())

def get_buffer_length(joern_nodes, v, node_type):
    line_nodes = get_line_nodes(joern_nodes, v)
    if node_type == "AF":
        arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]

        assert len(arg_nodes) == 1, f"ERROR: Buffer alloc with {len(arg_nodes)} arguments"

        return evaluate_size(arg_nodes[0]["code"].strip())
    elif node_type == "AD":
        size_str = [node for node in line_nodes if node["type"] == "IdentifierDeclType"][0]["code"]

        return evaluate_size(size_str)
    return -1

def get_buffer_alloc_dest(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    asgnmnt_nodes = [node for node in line_nodes if node["type"] == "AssignmentExpression"]

    assert len(asgnmnt_nodes) == 1, f"ERROR: Buffer alloc with {len(asgnmnt_nodes)} assignment expressions"

    return asgnmnt_nodes[0]["code"].split("=", maxsplit=1)[0].strip()

def get_array_indexing_info(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arr_indexing_node = [node for node in line_nodes if node["type"] == "ArrayIndexing"][0]
    dest_arr, dest_index = [part.strip() for part in arr_indexing_node["code"].split("[", maxsplit=1)]
    dest_index = dest_index.replace("]", "").strip()

    return dest_arr, dest_index

def get_deallocated_buffer(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    arg_nodes = [node for node in line_nodes if node["type"] == "Argument"]
    assert len(arg_nodes) == 1, f"ERROR: Buffer dealloc with {len(arg_nodes)} arguments"

    return arg_nodes[0]["code"].strip()

def mu(nodes_dir, key, v):
    nodes_path = join(nodes_dir, "nodes.csv")
    joern_nodes = read_csv(nodes_path)

    if key == "type":
        return get_node_type(joern_nodes, v)
    if key == "arg_dest":
        return get_buffer_write_dest(joern_nodes, v)
    if key == "arg_src":
        return get_buffer_write_src(joern_nodes, v)
    if key == "arg_count":
        return get_buffer_write_byte_count(joern_nodes, v)
    if key == "len":
        return get_buffer_length(joern_nodes, v, mu(nodes_dir, "type", v))
    if key == "dest":
        return get_buffer_alloc_dest(joern_nodes, v)
    if key == "arr_idx":
        return get_array_indexing_info(joern_nodes, v)
    if key == "dealloc_buff":
        return get_deallocated_buffer(joern_nodes, v)
    if key in ["sensi_read_callee", "sensi_write_callee"]:
        return get_called_sensi_funcs(joern_nodes, v, key)

    return None

if __name__ == "__main__":
    pass