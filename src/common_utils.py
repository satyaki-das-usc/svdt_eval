import networkx as nx

from argparse import ArgumentParser
from os.path import exists, join
from typing import List, Set, Tuple, Dict

def parse_args():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c",
                            "--config",
                            help="Path to YAML configuration file",
                            default="configs/dwk.yaml",
                            type=str)
    arg_parser.add_argument("--f",
                            help="Dummy",
                            type=str)
    
    args = arg_parser.parse_args()

    return args

def read_csv(csv_file_path: str) -> List:
    assert exists(csv_file_path), f"no {csv_file_path}"
    data = []
    with open(csv_file_path) as fp:
        header = fp.readline()
        header = header.strip()
        h_parts = [hp.strip() for hp in header.split('\t')]
        for line in fp:
            line = line.strip()
            instance = {}
            lparts = line.split('\t')
            for i, hp in enumerate(h_parts):
                if i < len(lparts):
                    content = lparts[i].strip()
                else:
                    content = ''
                instance[hp] = content
            data.append(instance)
        return data

def extract_nodes_with_location_info(nodes):
    """
    Will return an array identifying the indices of those nodes in nodes array
    """

    node_id_to_line_number = {}
    for node in nodes:
        assert isinstance(node, dict)
        if 'location' in node.keys():
            location = node['location']
            if location == '':
                continue
            line_num = int(location.split(':')[0])
            node_id = node['key'].strip()
            node_id_to_line_number[node_id] = line_num
    return node_id_to_line_number

def build_CPG(code_path: str,
              source_path: str) -> Tuple[nx.DiGraph, Dict[str, Set[int]]]:
    nodes_path = join(code_path, "nodes.csv")
    edges_path = join(code_path, "edges.csv")
    if not exists(nodes_path) or not exists(edges_path):
        print(nodes_path)
        print('here')
        return None, None
    nodes = read_csv(nodes_path)
    edges = read_csv(edges_path)
    if len(nodes) == 0:
        return None, None

    PDG = nx.DiGraph(file_paths=[source_path])
    control_edges, data_edges, post_dom_edges, def_edges, use_edges = list(), list(), list(), list(), list()
    node_id_to_ln = extract_nodes_with_location_info(nodes)
    for edge in edges:
        edge_type = edge['type'].strip()
        if True:
            start_node_id = edge['start'].strip()
            end_node_id = edge['end'].strip()
            if start_node_id not in node_id_to_ln.keys(
            ) or end_node_id not in node_id_to_ln.keys():
                continue
            start_ln = node_id_to_ln[start_node_id]
            end_ln = node_id_to_ln[end_node_id]
            if edge_type == 'CONTROLS':  # Control
                control_edges.append((start_ln, end_ln, {"label": "CONTROLS"}))
            if edge_type == 'REACHES':  # Data
                data_edges.append((start_ln, end_ln, {"label": "REACHES", "var": edge["var"].strip()}))
            if edge_type == 'POST_DOM': # Post dominance
                post_dom_edges.append((start_ln, end_ln, {"label": "POST_DOM"}))
            if edge_type == 'DEF': # Definition
                def_edges.append((start_ln, end_ln, {"label": "DEF"}))
            if edge_type == 'USE': # Use
                use_edges.append((start_ln, end_ln, {"label": "USE"}))
    PDG.add_edges_from(control_edges)
    PDG.add_edges_from(data_edges)
    PDG.add_edges_from(post_dom_edges)
    PDG.add_edges_from(def_edges)
    PDG.add_edges_from(use_edges)
    return PDG

if __name__ == "__main__":
    pass