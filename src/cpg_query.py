from os.path import join

from src.common_utils import read_csv

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
        return None
    
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

def is_buffer_copy_function_call(joern_nodes, v):
    line_nodes = get_line_nodes(joern_nodes, v)
    if len([node for node in line_nodes if node["type"] == "CallExpression"]) == 0:
        return False
    return len([node for node in line_nodes if node["type"] == "Callee" and node["code"].strip() == "strncpy"]) > 0

def get_node_type(joern_nodes, v):
    if is_buffer_write_function_call(joern_nodes, v):
        return "WF"
    elif is_buffer_allocation_function_call(joern_nodes, v):
        return "AF"
    elif is_arr_decl(joern_nodes, v):
        return "AD"
    elif is_buffer_copy_function_call(joern_nodes, v):
        return "CF"
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
        "char[": "1*",
        "unsignedchar[": "1*",
        "signedchar[": "1*",
        "int[": "4*",
        "unsignedint[": "4*",
        "short[": "2*",
        "unsignedshort[": "2*",
        "long[": "8*",
        "unsignedlong[": "8*",
    }
    for key, value in replacements.items():
        expression = expression.replace(key, value)

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

def mu(nodes_dir, key, v, u=None):
    nodes_path = join(nodes_dir, "nodes.csv")
    joern_nodes = read_csv(nodes_path)
    
    if u is not None:
        edges_path = join(nodes_dir, "edges.csv")
        joern_edges = read_csv(edges_path)
        uid = joern_nodes[get_start_node_idx(joern_nodes, u)]["key"]
        vid = joern_nodes[get_start_node_idx(joern_nodes, v)]["key"]

        data_edges = [edge for edge in joern_edges if edge["start"] == uid and edge["end"] == vid and edge["type"] == "REACHES"]
        if len(data_edges) == 0:
            return ""

        return data_edges[0][key]

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
    return None

if __name__ == "__main__":
    pass