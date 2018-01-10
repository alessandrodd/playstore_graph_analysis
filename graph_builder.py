import datetime
import json
import os
import time

import snap

from db_interface import get_edge_number, get_all

id_pkg_dict = {}


def get_id_from_package(graph, package):
    node_id = id_pkg_dict.get(package, -1)
    if node_id == -1:
        node_id = graph.AddNode(-1)
        id_pkg_dict[package] = node_id
        graph.AddStrAttrDatN(node_id, package, "pkg")
    return node_id


def create_play_store_graph(output_graph_path):
    start = time.time()
    docs = get_all()
    n = docs.count()
    print("# Nodes: {0}".format(n))
    m = get_edge_number()
    print("# Edges: {0}".format(m))
    graph = snap.TNEANet.New(n, m)
    i = 0
    for doc in docs:
        if i % 10000 == 0:
            print("{0} {1:.2f}% completed".format(datetime.datetime.now(), float(i) / n * 100.0))
        package = doc.get('docid')
        node_id = get_id_from_package(graph, package)
        similar_packages = doc.get('similarTo')
        for p in similar_packages:
            target_id = get_id_from_package(graph, p)
            graph.AddEdge(node_id, target_id)
        i += 1
    end = time.time()
    print("Saving to binary")
    graph_path = os.path.abspath(output_graph_path + ".graph")
    fout = snap.TFOut(graph_path)
    graph.Save(fout)
    fout.Flush()
    print("Saving Edge List")
    edgelist_path = os.path.abspath(output_graph_path + ".edgelist.txt")
    snap.SaveEdgeList(graph, edgelist_path, "Google Play Store snapshot graph, period 10/08/2017 - 07/09/2017")
    print("Saving dictionary")
    dict_path = os.path.abspath(output_graph_path + ".pkg_to_id_dict.json")
    with open(dict_path, 'w') as f:
        f.write(json.dumps(id_pkg_dict, indent=4))
    print("Total time: {0}".format(end - start))
