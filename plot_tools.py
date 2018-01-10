import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import Normalize

import snap


def snap_graph_to_networkx(snap_graph):
    if isinstance(snap_graph, snap.TUNGraph):
        nx_graph = nx.Graph()
    else:
        nx_graph = nx.DiGraph()
    for edge in snap_graph.Edges():
        nx_graph.add_edge(edge.GetSrcNId(), edge.GetDstNId())
    return nx_graph


def get_labels_subset(id_pkg_dict, subgraph):
    labels_dict = {}
    for edge in subgraph.Edges():
        labels_dict[edge.GetSrcNId()] = ellipsize_text(id_pkg_dict[edge.GetSrcNId()], 18)
        labels_dict[edge.GetDstNId()] = ellipsize_text(id_pkg_dict[edge.GetDstNId()], 18)
    return labels_dict


def plot_subgraph_colored(snap_graph, labels_dict, values_dict, value_label, title, output, cmap="autumn_r"):
    nx_graph = snap_graph_to_networkx(snap_graph)

    # functions used for color interpolation
    min_val = None
    max_val = None
    if values_dict:
        min_val = min(values_dict.values())
        max_val = max(values_dict.values())

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title(title)
    ax.axis('off')
    pos = nx.spring_layout(nx_graph, k=0.4, iterations=10000)
    nx.draw_networkx(nx_graph, pos=pos, linewidths=0.1, alpha=0.8, width=0.1, edge_color="grey", font_size=4,
                     font_weight='bold', font_color="green",
                     node_color=[values_dict[nodeid] for nodeid in nx_graph.nodes()], cmap=cmap,
                     labels=labels_dict, ax=ax)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=Normalize(vmin=min_val, vmax=max_val))
    sm._A = []
    cb = plt.colorbar(sm, orientation='horizontal', aspect=100)
    cb.set_label(value_label)

    plt.tight_layout()

    fig.savefig(output)


def ellipsize_text(text, max_length):
    if len(text) <= max_length + 4:
        return text
    start = text[:max_length / 2]
    end = text[len(text) - max_length / 2:]
    return start + ".." + end


def plot_subgraph(graph, nodes, output, title):
    node_ids_vector = snap.TIntV()
    labels = snap.TIntStrH()
    for pair in nodes:
        if pair[0] not in node_ids_vector:
            node_ids_vector.Add(pair[0])
            pkg = graph.GetStrAttrDatN(pair[0], "pkg")
            labels[pair[0]] = ellipsize_text(pkg, 30)
    subgraph = snap.GetSubGraph(graph, node_ids_vector)
    snap.DrawGViz(subgraph, snap.gvlNeato, output, title, labels)


def generate_histogram(buckets, title, x_label, y_label, output):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    indexes = np.arange(min(buckets.keys()) - 1, max(buckets.keys()) + 2)  # the x locations for the groups
    width = 0.1  # the width of the bars

    ax.set_yscale('log')
    ax.grid(zorder=0, axis="y")

    bars1 = ax.bar(indexes, [buckets.get(i, 0) for i in indexes], align='center', color='blue')

    # axes and labels
    ax.set_xlim(indexes[0] - 1, indexes[-1] + 1)
    ax.set_ylim(min(buckets.values()) - width, max(buckets.values()) + width)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title, fontsize=10)
    # x_tick_marks = [str(i) for i in range(1, 6)]
    # ax.set_xticks(ind + width)
    # xtickNames = ax.set_xticklabels(xTickMarks)
    # plt.setp(xtickNames, rotation=45, fontsize=10)

    fig.savefig(output)


def generate_histrogram_strings(buckets, title, x_label, y_label, output):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sorted_keys = sorted(buckets.keys(), key=lambda item: int(''.join(x for x in item if x.isdigit())))
    indexes = np.arange(0, len(sorted_keys))  # the x locations for the groups
    width = 0.1  # the width of the bars

    ax.set_yscale('log')
    ax.grid(zorder=0, axis="y")

    bars1 = ax.bar(indexes, [buckets.get(sorted_keys[i], 0) for i in indexes], align='center', color='blue')

    # axes and labels
    ax.set_ylim(0.5, max(buckets.values()) + 1)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    ax.xaxis.set_major_locator(plt.FixedLocator(indexes))
    ax.xaxis.set_major_formatter(plt.FixedFormatter(sorted_keys))
    labels = ax.get_xticklabels()
    for tick in labels:
        tick.set_rotation(90)

    plt.tight_layout()

    fig.savefig(output)


def generate_histogram_from_data(data, bins, title, x_label, y_label, output):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_yscale('log')
    ax.grid(zorder=0, axis="both")
    ax.hist(data, bins=bins)

    # axes and labels
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    labels = ax.get_xticklabels()
    for tick in labels:
        tick.set_rotation(90)
        tick.set_ha = 'left'
    ax.set_title(title)

    plt.tight_layout()

    fig.savefig(output)


def generate_histogram_from_data_log(data, bins, title, x_label, y_label, output):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.grid(zorder=0, axis="both")
    ax.hist(data, bins=bins)

    # axes and labels
    ax.set_ylim(0.5, max(data) + 1)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    plt.tight_layout()

    fig.savefig(output)


def generate_histogram_from_timestamps(timestamps, title, x_label, y_label, output):
    mpl_data = mdates.epoch2num(timestamps)
    bins = int((max(timestamps) - min(timestamps)) / (24 * 60 * 60 * 30) + 1)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_yscale('log')
    ax.grid(zorder=0, axis="both")
    ax.hist(mpl_data, bins=bins)

    # axes and labels
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b.%y'))

    plt.tight_layout()

    fig.savefig(output)
