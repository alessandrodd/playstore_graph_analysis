import datetime
import heapq
import json
import numpy as np
import os
import re
from collections import OrderedDict
from operator import itemgetter

from rake_nltk import Rake

import date_tools
import plot_tools
from db_interface import get_creators, get_all, get_permissions, get_package_by_permissions_size, \
    get_apps_downloads, get_apps_files, get_apps_upload_date, get_apps_bayesian_ratings, get_apps_star_ratings, \
    get_descriptions


def compute_db_statistics(stats_path, packages, title, overwrite):
    stats_abs_path = os.path.abspath(stats_path)
    json_path = os.path.abspath(stats_abs_path + ".db_statistics.json")
    if os.path.isfile(json_path):
        with open(json_path, "r") as f:
            statistics = json.load(f, object_pairs_hook=OrderedDict)
    else:
        statistics = OrderedDict()

    n_apps = get_all(packages).count()

    # statistics about number of downloads
    downloads_histogram_path = os.path.abspath(stats_abs_path + ".downloads.eps")
    if not os.path.isfile(downloads_histogram_path) or overwrite:
        print("{0} Computing # downloads histogram".format(datetime.datetime.now()))
        dl_buckets = {}
        for doc in get_apps_downloads(packages):
            try:
                n_downloads = doc.get("details").get("appDetails").get("numDownloads")
                if n_downloads is None:
                    continue
                n_downloads = n_downloads.split("+")[0] + "+"
                dl_buckets[n_downloads] = dl_buckets.get(n_downloads, 0) + 1
            except AttributeError:
                continue
        plot_tools.generate_histrogram_strings(dl_buckets,
                                               "{0}\nNumber of apps distribution per number of downloads".format(title),
                                               "# downloads, lower bound", "# apps", downloads_histogram_path)

    # statistics about app size
    size_histogram_path = os.path.abspath(stats_abs_path + ".apps_size.eps")
    if not os.path.isfile(size_histogram_path) or "biggest_apps" not in statistics or overwrite:
        print("{0} Computing app size statistics".format(datetime.datetime.now()))
        top_10 = []
        bottom_10 = []
        sizes = []
        for doc in get_apps_files(packages):
            try:
                f = doc.get("details").get("appDetails").get("file")
                if f:
                    size = f[0].get("size")
                else:
                    continue
            except AttributeError:
                continue
            if size is None:
                continue
            else:
                size = int(size)
            if not top_10 or size > min(top_10, key=itemgetter(1))[1]:
                pkg = doc.get("docid")
                if len(top_10) == 10:
                    top_10.remove(min(top_10, key=itemgetter(1)))
                top_10.append((pkg, size))

            if not bottom_10 or size < max(bottom_10, key=itemgetter(1))[1]:
                pkg = doc.get("docid")
                if len(bottom_10) == 10:
                    bottom_10.remove(max(bottom_10, key=itemgetter(1)))
                bottom_10.append((pkg, size))

            sizes.append(size)
        top_10.sort(key=itemgetter(1))
        bottom_10.sort(key=itemgetter(1))
        statistics["biggest_apps"] = list(reversed(top_10))
        statistics["smallest_apps"] = bottom_10
        statistics["avg_app_size"] = np.mean(sizes)
        statistics["stdev_app_size"] = np.std(sizes)
        statistics["95perc_app_size"] = np.percentile(sizes, 95)
        statistics["99perc_app_size"] = np.percentile(sizes, 99)
        print("{0} Computing apps size histogram".format(datetime.datetime.now()))
        plot_tools.generate_histogram_from_data_log(sizes,
                                                    [1000, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000,
                                                     10000000, 50000000, 100000000, 500000000, 1000000000,
                                                     5000000000],
                                                    "{0}\nNumber of apps distribution per app size".format(title),
                                                    "app size (bytes)", "# apps", size_histogram_path)

    # statistics about latest apps update
    update_histogram_path = os.path.abspath(stats_abs_path + ".app_last_updates.eps")
    if not os.path.isfile(update_histogram_path) or overwrite:
        print("{0} Computing apps updates histogram".format(datetime.datetime.now()))
        timestamps = []
        for doc in get_apps_upload_date(packages):
            try:
                date = doc.get("details").get("appDetails").get("uploadDate")
                if not date:
                    continue
                upload_timestamp = date_tools.play_store_timestamp_to_unix_timestamp(date)
                timestamps.append(upload_timestamp)
            except AttributeError:
                continue
        statistics["avg_app_timestamp"] = np.mean(timestamps)
        plot_tools.generate_histogram_from_timestamps(timestamps,
                                                      "{0}\nNumber of apps distribution per last update time".format(
                                                          title),
                                                      "date of last update", "# apps", update_histogram_path)

    # statistics about bayesian rating
    bayesian_histogram_path = os.path.abspath(stats_abs_path + ".bayesian_ratings.eps")
    if not os.path.isfile(bayesian_histogram_path) or "avg_bayesian_rating" not in statistics or overwrite:
        print("{0} Computing apps bayesian rating statistics".format(datetime.datetime.now()))
        top_10 = []
        ratings = []
        for doc in get_apps_bayesian_ratings(packages):
            try:
                rating = doc.get("aggregateRating").get("bayesianMeanRating")
                if rating:
                    rating = float(rating)
                else:
                    continue
            except AttributeError:
                continue
            if not top_10 or rating > min(top_10, key=itemgetter(1))[1]:
                pkg = doc.get("docid")
                if len(top_10) == 10:
                    top_10.remove(min(top_10, key=itemgetter(1)))
                top_10.append((pkg, rating))
            ratings.append(rating)

        top_10.sort(key=itemgetter(1))
        statistics["top_bayesian_rated_apps"] = list(reversed(top_10))
        statistics["avg_bayesian_rating"] = np.mean(ratings)
        statistics["stdev_bayesian_rating"] = np.std(ratings)
        statistics["95perc_bayesian_rating"] = np.percentile(ratings, 95)
        statistics["99perc_bayesian_rating"] = np.percentile(ratings, 99)
        print("{0} Computing bayesian rating histogram".format(datetime.datetime.now()))
        # small dirty trick to force bins alignment
        ratings.append(1)
        ratings.append(5)
        plot_tools.generate_histogram_from_data(ratings, 16,
                                                "{0}\nNumber of apps distribution per Bayesian rating".format(title),
                                                "Bayesian rating", "# apps", bayesian_histogram_path)

    # statistics about star rating
    star_histogram_path = os.path.abspath(stats_abs_path + ".star_ratings.eps")
    if not os.path.isfile(star_histogram_path) or "avg_star_rating" not in statistics or overwrite:
        print("{0} Computing apps star rating statistics".format(datetime.datetime.now()))
        ratings = []
        for doc in get_apps_star_ratings(packages):
            try:
                rating = doc.get("aggregateRating").get("starRating")
                if rating:
                    rating = float(rating)
                else:
                    continue
            except AttributeError:
                continue
            ratings.append(rating)

        statistics["avg_star_rating"] = np.mean(ratings)
        statistics["stdev_star_rating"] = np.std(ratings)
        statistics["95perc_star_rating"] = np.percentile(ratings, 95)
        statistics["99perc_star_rating"] = np.percentile(ratings, 99)
        print("{0} Computing star rating histogram".format(datetime.datetime.now()))
        plot_tools.generate_histogram_from_data(ratings, 16,
                                                "{0}\nNumber of apps distribution per star rating".format(title),
                                                "star rating", "# apps", star_histogram_path)

    # statistics about permissions request
    permissions_histogram_path = os.path.abspath(stats_abs_path + ".permissions_requests.eps")
    if not os.path.isfile(permissions_histogram_path) or "n_permissions" not in statistics \
            or "avg_permissions_per_app" not in statistics or "most_requested_permissions" not in statistics \
            or "top_permissions_requesters" not in statistics or overwrite:
        print("{0} Computing # of permissions".format(datetime.datetime.now()))
        n_permissions_buckets = {}
        permissions_counter = {}
        n_permissions_list = []
        for doc in get_permissions(packages):
            try:
                permissions = doc.get("details").get("appDetails").get("permission")
            except AttributeError:
                permissions = []
            if permissions is None:
                permissions = []
            permissions = [p for p in permissions if p.upper().startswith('ANDROID.PERMISSION')]
            n_permissions_list.append(len(permissions))
            n_permissions_buckets[len(permissions)] = n_permissions_buckets.get(len(permissions), 0) + 1
            for permission in permissions:
                permission = permission.upper()
                permissions_counter[permission] = permissions_counter.get(permission, 0) + 1
        statistics["n_permissions"] = len(permissions_counter.keys())
        print("{0} Computing avg and std permissions per app".format(datetime.datetime.now()))
        statistics["avg_permissions_per_app"] = np.mean(n_permissions_list)
        statistics["stdev_permissions_per_app"] = np.std(n_permissions_list)
        statistics["95perc_permissions_per_app"] = np.percentile(n_permissions_list, 95)
        statistics["99perc_permissions_per_app"] = np.percentile(n_permissions_list, 99)

        print("{0} Computing top and bottom 10 requested permissions".format(datetime.datetime.now()))
        top_10 = heapq.nlargest(10, permissions_counter, key=permissions_counter.get)
        top_10_pairs = []
        for permission in top_10:
            top_10_pairs.append((permission, float(permissions_counter[permission]) / n_apps * 100))
        statistics["most_requested_permissions"] = top_10_pairs

        bottom_10 = heapq.nsmallest(10, permissions_counter, key=permissions_counter.get)
        bottom_10_pairs = []
        for permission in bottom_10:
            bottom_10_pairs.append((permission, float(permissions_counter[permission]) / n_apps * 100))
        statistics["less_requested_permissions"] = bottom_10_pairs

        print("{0} Computing # permissions requests histogram".format(datetime.datetime.now()))
        plot_tools.generate_histogram(n_permissions_buckets,
                                      "{0}\nNumber of apps distribution per number of permissions requested".format(
                                          title),
                                      "# permissions requested", "# apps", permissions_histogram_path)

        print("{0} Computing top permissions requesters".format(datetime.datetime.now()))
        top_10 = heapq.nlargest(10, n_permissions_buckets.keys())
        top_10_pairs = []
        counter = 0
        for n_permissions in top_10:
            docs = get_package_by_permissions_size(n_permissions)
            for doc in docs:
                top_10_pairs.append((doc.get("docid"), n_permissions))
                counter += 1
                if counter == 10:
                    break
            if counter == 10:
                break
        statistics["top_permissions_requesters"] = top_10_pairs

    creators_histogram_path = os.path.abspath(stats_abs_path + ".creators_productivity.eps")
    if not os.path.isfile(creators_histogram_path) or "n_creators" not in statistics \
            or "most_prolific_creators" not in statistics or "avg_apps_per_creator" not in statistics \
            or "95perc_apps_per_creator" not in statistics or overwrite:

        print("{0} Computing # of creators".format(datetime.datetime.now()))
        buckets = {}
        for doc in get_creators(packages):
            creator = doc.get("creator")
            buckets[creator] = buckets.get(creator, 0) + 1
        statistics["n_apps"] = n_apps
        statistics["n_creators"] = len(buckets.keys())

        print("{0} Computing top 10 prolific creators".format(datetime.datetime.now()))
        top_10 = heapq.nlargest(10, buckets, key=buckets.get)
        top_10_pairs = []
        for developer in top_10:
            top_10_pairs.append((developer, buckets[developer]))
        statistics["most_prolific_creators"] = top_10_pairs

        print("{0} Computing creators productivity histogram excluding top 10".format(datetime.datetime.now()))
        productivity_buckets = {}
        for key in buckets.keys():
            if key in top_10:
                continue
            productivity_buckets[buckets[key]] = productivity_buckets.get(buckets[key], 0) + 1

        plot_tools.generate_histogram(productivity_buckets,
                                      "{0}\nNumber of developers distribution per number of apps released\n".format(
                                          title) +
                                      "(excluding top 10 most prolific developers)",
                                      "# apps released", "# developers", creators_histogram_path)

        print("{0} Computing avg and std apps per creator".format(datetime.datetime.now()))
        statistics["avg_apps_per_creator"] = np.mean(buckets.values())
        statistics["stdev_apps_per_creator"] = np.std(buckets.values())
        statistics["95perc_apps_per_creator"] = np.percentile(buckets.values(), 95)
        statistics["99perc_apps_per_creator"] = np.percentile(buckets.values(), 99)

    with open(json_path, 'w') as outfile:
        json.dump(statistics, outfile, indent=2)


def extract_keywords(dump_path, packages):
    print("{0} Gathering descriptions and computing keywords...".format(datetime.datetime.now()))
    rake = Rake()
    keywords = {}
    for doc in get_descriptions(packages):
        try:
            if "translatedDescriptionHtml" in doc:
                html_description = unicode(doc.get("translatedDescriptionHtml"))
            else:
                html_description = unicode(doc.get("descriptionHtml"))
            # remove html elements
            description = re.sub(r'<.*?>', '', html_description)
            # substitute non-ascii chars with stop words (e.g. dot)
            description = re.sub(r'[^\x00-\x7F]+', ' . ', description)
            rake.extract_keywords_from_text(description)
            ranking = rake.get_ranked_phrases_with_scores()
            for pair in ranking:
                keywords[pair[1]] = keywords.get(pair[1], 0) + pair[0]
        except AttributeError:
            continue
    sorted_keywords = sorted(keywords.items(), key=itemgetter(1))
    with open(dump_path, 'w') as outfile:
        json.dump(sorted_keywords, outfile, indent=2)
