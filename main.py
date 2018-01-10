import argparse

from db_analyzer import compute_db_statistics, extract_keywords
from graph_analyzer import compute_graph_statistics, get_top_packages
from graph_builder import create_play_store_graph


def main():
    parser = argparse.ArgumentParser(
        description='Play Store crawl to graph converter and analyzer', add_help=True)
    parser.add_argument('--create-graph', action="store", dest='output_graph_path',
                        help='Creates a graph of the Google Play Store using the data collected '
                             'during the crawling operation and stored in a MongoDB instance. '
                             'OUTPUT_GRAPH_PATH should NOT specify the file extension.')
    parser.add_argument('--overwrite', action="store_true", dest='overwrite',
                        default=False, help='Overwrite the already computed files')
    parser.add_argument('--packages', action="store", type=str, nargs='+', dest='packages',
                        help='Consider only the submitted packages')
    group0 = parser.add_argument_group()
    group0.add_argument('--compute-statistics', action="store", dest='input_graph_path',
                        help='Analyzes the graph and computes several statistics. Specify the '
                             'path of the .graph file to analyze.')
    group1 = parser.add_argument_group()
    group1.add_argument('--compute-db-statistics', action="store", dest='output_stats_path',
                        help='Compute several Play Store statistics directly using the data on the DB. '
                             'OUTPUT_STATS_PATH should NOT specify the file extension (multiple files are created)')
    group1.add_argument('--title', action="store", dest='title',
                        help='Main title for the plotted graphs')
    group2 = parser.add_argument_group()
    group2.add_argument('--extract-keywords', action="store", dest='keywords_dump_path',
                        help='Extract keywords from app descriptions and dumps them to a text file')
    group3 = parser.add_argument_group()
    group3.add_argument('--get-top-packages', action="store", nargs=2, dest="top_packages",
                        metavar=('N_PACKAGES', 'GRAPH_PATH'),
                        help='Returns a list of the top N_PACKAGES based on PageRank')

    results = parser.parse_args()
    if results.output_graph_path:
        create_play_store_graph(results.output_graph_path)
        return

    if results.input_graph_path:
        graph_path = results.input_graph_path
        overwrite = results.overwrite
        compute_graph_statistics(graph_path, overwrite)
        return

    if results.top_packages:
        n = int(results.top_packages[0])
        graph_path = results.top_packages[1]
        packages = get_top_packages(graph_path, n)
        output_string = ""
        for pkg in packages:
            output_string += pkg
            output_string += " "
        print(output_string)
        return

    if results.output_stats_path:
        packages = None
        title = "Play Store"
        if results.packages:
            packages = results.packages
        if results.title:
            title = results.title
        compute_db_statistics(results.output_stats_path, packages, title, results.overwrite)
        return

    if results.keywords_dump_path:
        keywords_path = results.keywords_dump_path
        packages = None
        if results.packages:
            packages = results.packages
        extract_keywords(keywords_path, packages)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
