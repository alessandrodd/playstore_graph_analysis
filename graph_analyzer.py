import datetime
import json
import os
from collections import OrderedDict
from operator import itemgetter

import snap

from plot_tools import plot_subgraph_colored, get_labels_subset


def get_top_nodes_from_hashtable(hashtable, limit=20):
    top_nodes = []
    for node in hashtable:
        value = hashtable[node]
        if not top_nodes or value >= min(top_nodes, key=itemgetter(1))[1]:
            if len(top_nodes) == limit:
                top_nodes.remove(min(top_nodes, key=itemgetter(1)))
            top_nodes.append((node, value))
    return top_nodes


def get_subgraph(graph, nodes_ids):
    node_ids_vector = snap.TIntV()
    for node_id in nodes_ids:
        if node_id not in node_ids_vector:
            node_ids_vector.Add(node_id)
    subgraph = snap.GetSubGraph(graph, node_ids_vector)
    return subgraph


def snap_hashtable_to_dict(snap_ht, keys):
    d = {}
    for key in keys:
        d[key] = snap_ht[key]
    return d


def compute_graph_statistics(graph_path, overwrite, compute_betweenness=False):
    graph_abs_path = os.path.abspath(graph_path)
    graph_name = os.path.basename(graph_abs_path).replace(".graph", "")
    fin = snap.TFIn(graph_abs_path)
    graph = snap.TNEANet.Load(fin)

    # rebuild the id => pkg dictionary
    id_pkg_dict = {}
    for node in graph.Nodes():
        id_pkg_dict[node.GetId()] = graph.GetStrAttrDatN(node.GetId(), "pkg")
    directory = os.path.dirname(os.path.abspath(graph_path))
    json_path = os.path.join(directory, graph_name + "_statistics.json")
    if os.path.isfile(json_path):
        with open(json_path, "r") as f:
            statistics = json.load(f, object_pairs_hook=OrderedDict)
    else:
        statistics = OrderedDict()

    # snap.py doesn't suport absolute paths for some operations. Let's cd to the directory
    os.chdir(directory)

    # general statistics
    output = os.path.join(directory, graph_name + "_main_statistics.txt")
    if not os.path.isfile(output) or overwrite:
        print("{0} Computing general statistics".format(datetime.datetime.now()))
        snap.PrintInfo(graph, "Play Store Graph -- main statistics", output, False)

    # info about the nodes with the max in degree
    if "max_in_degree" not in statistics or overwrite:
        print("{0} Computing max indegree".format(datetime.datetime.now()))
        max_in_deg_id = snap.GetMxInDegNId(graph)
        iterator = graph.GetNI(max_in_deg_id)
        max_in_deg = iterator.GetInDeg()
        max_in_deg_pkg = graph.GetStrAttrDatN(max_in_deg_id, "pkg")
        statistics["max_in_degree"] = max_in_deg
        statistics["max_in_degree_id"] = max_in_deg_id
        statistics["max_in_degree_pkg"] = max_in_deg_pkg

    # info about the nodes with the max out degree
    if "max_out_degree" not in statistics or overwrite:
        print("{0} Computing max outdegree".format(datetime.datetime.now()))
        max_out_deg_id = snap.GetMxOutDegNId(graph)
        iterator = graph.GetNI(max_out_deg_id)
        max_out_deg = iterator.GetOutDeg()
        max_out_deg_pkg = graph.GetStrAttrDatN(max_out_deg_id, "pkg")
        statistics["max_out_degree"] = max_out_deg
        statistics["max_out_degree_id"] = max_out_deg_id
        statistics["max_out_degree_pkg"] = max_out_deg_pkg

    # pagerank statistics
    output = graph_name + "_topNpagerank.eps"
    if not os.path.isfile(output) or "top_n_pagerank" not in statistics or overwrite:
        print("{0} Computing top 20 nodes with highest pagerank".format(datetime.datetime.now()))
        data_file = graph_name + "_pageranks"
        prank_hashtable = snap.TIntFltH()
        if not os.path.isfile(data_file) or overwrite:
            # Damping Factor: 0.85, Convergence difference: 1e-4, MaxIter: 100
            snap.GetPageRank(graph, prank_hashtable, 0.85)
            fout = snap.TFOut(data_file)
            prank_hashtable.Save(fout)
        else:
            fin = snap.TFIn(data_file)
            prank_hashtable.Load(fin)

        top_n = get_top_nodes_from_hashtable(prank_hashtable)
        top_n.sort(key=itemgetter(1))
        if "top_n_pagerank" not in statistics or overwrite:
            top_n_labeled = []
            for pair in top_n:
                top_n_labeled.append((id_pkg_dict[pair[0]], pair[1]))
            statistics["top_n_pagerank"] = list(reversed(top_n_labeled))

        if not os.path.isfile(output) or overwrite:
            # let's build a subgraph induced on the top 20 pagerank nodes
            subgraph = get_subgraph(graph, [x[0] for x in top_n])
            labels_dict = get_labels_subset(id_pkg_dict, subgraph)
            values = snap_hashtable_to_dict(prank_hashtable, [x[0] for x in top_n])
            plot_subgraph_colored(subgraph, labels_dict, values, "PageRank",
                                  "Play Store Graph - top 20 PageRank nodes", output, "autumn_r")

    # betweeness statistics
    output = graph_name + "_topNbetweenness.eps"
    if compute_betweenness and (not os.path.isfile(output) or "betweenness" not in statistics or overwrite):
        print("{0} Computing top 20 nodes with highest betweenness".format(datetime.datetime.now()))
        data_file1 = graph_name + "_node_betweenness"
        data_file2 = graph_name + "_edge_betweenness"
        node_betwenness_hashtable = snap.TIntFltH()
        edge_betwenness_hashtable = snap.TIntPrFltH()
        if not os.path.isfile(data_file1) or not os.path.isfile(data_file2) or overwrite:
            snap.GetBetweennessCentr(graph, node_betwenness_hashtable, edge_betwenness_hashtable, 0.85, True)
            fout = snap.TFOut(data_file1)
            node_betwenness_hashtable.Save(fout)
            fout = snap.TFOut(data_file2)
            edge_betwenness_hashtable.Save(fout)

        else:
            fin = snap.TFIn(data_file1)
            node_betwenness_hashtable.Load(fin)
            fin = snap.TFIn(data_file2)
            edge_betwenness_hashtable.Load(fin)  # unused, as now

        top_n = get_top_nodes_from_hashtable(node_betwenness_hashtable)
        top_n.sort(key=itemgetter(1))
        if "top_n_betweenness" not in statistics or overwrite:
            top_n_labeled = []
            for pair in top_n:
                top_n_labeled.append((id_pkg_dict[pair[0]], pair[1]))
            statistics["top_n_betweenness"] = list(reversed(top_n_labeled))

        if not os.path.isfile(output) or overwrite:
            # let's build a subgraph induced on the top 20 betweenness nodes
            subgraph = get_subgraph(graph, [x[0] for x in top_n])
            labels_dict = get_labels_subset(id_pkg_dict, subgraph)
            values = snap_hashtable_to_dict(node_betwenness_hashtable, [x[0] for x in top_n])
            plot_subgraph_colored(subgraph, labels_dict, values, "Betweenness",
                                  "Play Store Graph - top 20 Betweenness nodes", output)

    # HITS statistics
    output_hub = graph_name + "_topNhitshubs.eps"
    output_auth = graph_name + "_topNhitsauth.eps"
    if not os.path.isfile(output_hub) or not os.path.isfile(output_auth) or "top_n_hits_hubs" not in statistics \
            or "top_n_hits_authorities" not in statistics or overwrite:
        print("{0} Computing top 20 HITS hubs and auths".format(datetime.datetime.now()))
        data_file1 = graph_name + "_hits_hubs"
        data_file2 = graph_name + "_hits_auth"
        hubs_hashtable = snap.TIntFltH()
        auth_hashtable = snap.TIntFltH()
        if not os.path.isfile(data_file1) or not os.path.isfile(data_file2) or overwrite:
            # MaxIter = 20
            snap.GetHits(graph, hubs_hashtable, auth_hashtable, 20)
            fout = snap.TFOut(data_file1)
            hubs_hashtable.Save(fout)
            fout = snap.TFOut(data_file2)
            auth_hashtable.Save(fout)

        else:
            fin = snap.TFIn(data_file1)
            hubs_hashtable.Load(fin)
            fin = snap.TFIn(data_file2)
            auth_hashtable.Load(fin)

        top_n_hubs = get_top_nodes_from_hashtable(hubs_hashtable)
        top_n_hubs.sort(key=itemgetter(1))
        if "top_n_hits_hubs" not in statistics or overwrite:
            top_n_labeled = []
            for pair in top_n_hubs:
                top_n_labeled.append((id_pkg_dict[pair[0]], pair[1]))
            statistics["top_n_hits_hubs"] = list(reversed(top_n_labeled))

        top_n_auth = get_top_nodes_from_hashtable(auth_hashtable)
        top_n_auth.sort(key=itemgetter(1))
        if "top_n_hits_authorities" not in statistics or overwrite:
            top_n_labeled = []
            for pair in top_n_auth:
                top_n_labeled.append((id_pkg_dict[pair[0]], pair[1]))
            statistics["top_n_hits_authorities"] = list(reversed(top_n_labeled))

        if not os.path.isfile(output_hub) or not os.path.isfile(output_auth) or overwrite:
            nodes_subset = set()
            for pair in top_n_hubs:
                nodes_subset.add(pair[0])
            for pair in top_n_auth:
                nodes_subset.add(pair[0])

            # let's build a subgraph induced on the top N HITS auths and hubs nodes
            subgraph = get_subgraph(graph, nodes_subset)
            labels_dict = get_labels_subset(id_pkg_dict, subgraph)
            values = snap_hashtable_to_dict(hubs_hashtable, nodes_subset)
            values2 = snap_hashtable_to_dict(auth_hashtable, nodes_subset)
            plot_subgraph_colored(subgraph, labels_dict, values, "HITS - Hub Index",
                                  "Play Store Graph - top 20 HITS hubs + top 20 HITS authorities", output_hub, "bwr")
            plot_subgraph_colored(subgraph, labels_dict, values2, "HITS - Authority Index",
                                  "Play Store Graph - top 20 HITS hubs + top 20 HITS authorities", output_auth,
                                  "bwr_r")

    # indegree histogram
    output = graph_name + "_indegree"
    if not os.path.isfile("inDeg." + output + ".plt") or not os.path.isfile(
                            "inDeg." + output + ".tab") or not os.path.isfile("inDeg." + output + ".png") or overwrite:
        print("{0} Computing indegree distribution".format(datetime.datetime.now()))
        snap.PlotInDegDistr(graph, output, "Play Store Graph - in-degree Distribution")

    # outdegree histogram
    output = graph_name + "_outdegree"
    if not os.path.isfile("outDeg." + output + ".plt") or not os.path.isfile(
                            "outDeg." + output + ".tab") or not os.path.isfile(
                        "outDeg." + output + ".png") or overwrite:
        print("{0} Computing outdegree distribution".format(datetime.datetime.now()))
        snap.PlotOutDegDistr(graph, output, "Play Store Graph - out-degree Distribution")

    # strongly connected components print
    output = graph_name + "_scc"
    if not os.path.isfile("scc." + output + ".plt") or not os.path.isfile(
                            "scc." + output + ".tab") or not os.path.isfile("scc." + output + ".png") or overwrite:
        print("{0} Computing scc distribution".format(datetime.datetime.now()))
        snap.PlotSccDistr(graph, output, "Play Store Graph - strongly connected components distribution")

    # weakly connected components print
    output = graph_name + "_wcc"
    if not os.path.isfile("wcc." + output + ".plt") or not os.path.isfile(
                            "wcc." + output + ".tab") or not os.path.isfile("wcc." + output + ".png") or overwrite:
        print("{0} Computing wcc distribution".format(datetime.datetime.now()))
        snap.PlotWccDistr(graph, output, "Play Store Graph - weakly connected components distribution")

    # clustering coefficient distribution
    output = graph_name + "_cf"
    if not os.path.isfile("ccf." + output + ".plt") or not os.path.isfile(
                            "ccf." + output + ".tab") or not os.path.isfile("ccf." + output + ".png") or overwrite:
        print("{0} Computing cf distribution".format(datetime.datetime.now()))
        snap.PlotClustCf(graph, output, "Play Store Graph - clustering coefficient distribution")

    # shortest path distribution
    output = graph_name + "_hops"
    if not os.path.isfile("hop." + output + ".plt") or not os.path.isfile(
                            "hop." + output + ".tab") or not os.path.isfile("hop." + output + ".png") or overwrite:
        print("{0} Computing shortest path distribution".format(datetime.datetime.now()))
        snap.PlotHops(graph, output, "Play Store Graph - Cumulative Shortest Paths (hops) distribution", True)

    # k-core edges distribution
    output = graph_name + "_kcore_edges"
    if not os.path.isfile("coreEdges." + output + ".plt") or not os.path.isfile(
                            "coreEdges." + output + ".tab") or not os.path.isfile(
                        "coreEdges." + output + ".png") or overwrite:
        print("{0} Computing k-core edges distribution".format(datetime.datetime.now()))
        snap.PlotKCoreEdges(graph, output, "Play Store Graph - K-Core edges distribution")

    # k-core nodes distribution
    output = graph_name + "_kcore_nodes"
    if not os.path.isfile("coreNodes." + output + ".plt") or not os.path.isfile(
                            "coreNodes." + output + ".tab") or not os.path.isfile(
                        "coreNodes." + output + ".png") or overwrite:
        print("{0} Computing k-core nodes distribution".format(datetime.datetime.now()))
        snap.PlotKCoreNodes(graph, output, "Play Store Graph - K-Core nodes distribution")

    with open(json_path, 'w') as outfile:
        json.dump(statistics, outfile, indent=2)


def get_top_packages(graph_path, n):
    graph_abs_path = os.path.abspath(graph_path)
    graph_name = os.path.basename(graph_abs_path).replace(".graph", "")
    fin = snap.TFIn(graph_abs_path)
    graph = snap.TNEANet.Load(fin)
    # rebuild the id => pkg dictionary
    id_pkg_dict = {}
    for node in graph.Nodes():
        id_pkg_dict[node.GetId()] = graph.GetStrAttrDatN(node.GetId(), "pkg")
    directory = os.path.dirname(os.path.abspath(graph_path))

    # snap.py doesn't suport absolute paths for some operations. Let's cd to the directory
    os.chdir(directory)

    # print("{0} Computing top {0} nodes with highest pagerank".format(n, datetime.datetime.now()))
    data_file = graph_name + "_pageranks"
    prank_hashtable = snap.TIntFltH()
    if not os.path.isfile(data_file):
        # Damping Factor: 0.85, Convergence difference: 1e-4, MaxIter: 100
        snap.GetPageRank(graph, prank_hashtable, 0.85)
        fout = snap.TFOut(data_file)
        prank_hashtable.Save(fout)
    else:
        fin = snap.TFIn(data_file)
        prank_hashtable.Load(fin)

    top_n = get_top_nodes_from_hashtable(prank_hashtable, n)
    top_n.sort(key=itemgetter(1))
    top_packages = []
    for pair in top_n:
        top_packages.append(id_pkg_dict[pair[0]])
    return top_packages
