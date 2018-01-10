import pymongo
from pymongo.errors import AutoReconnect
from retry_decorator import retry

from config import dbconf

COL_PLAYSTORE_SNAPSHOT = "playstore_snapshot"
COL_PLAYSTORE = "playstore"

# remote db location
client = pymongo.MongoClient(dbconf.address, int(dbconf.port), username=dbconf.user, password=dbconf.password)
db = client[dbconf.name]
playstore_snapshot = db[COL_PLAYSTORE_SNAPSHOT]
playstore_detailed = db[COL_PLAYSTORE]


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apikey_unverified():
    document = playstore_snapshot.find_one({"verified": None})
    return document


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_all(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}})
    else:
        docs = playstore_snapshot.find()
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_creators(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}}, {"_id": 0, "creator": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "creator": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apps_downloads(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}}, {"_id": 0, "details.appDetails.numDownloads": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "details.appDetails.numDownloads": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apps_files(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}},
                                       {"_id": 0, "details.appDetails.file": 1, "docid": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "details.appDetails.file": 1, "docid": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apps_upload_date(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}}, {"_id": 0, "details.appDetails.uploadDate": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "details.appDetails.uploadDate": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apps_bayesian_ratings(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}},
                                       {"_id": 0, "aggregateRating.bayesianMeanRating": 1, "docid": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "aggregateRating.bayesianMeanRating": 1, "docid": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_apps_star_ratings(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}},
                                       {"_id": 0, "aggregateRating.starRating": 1, "docid": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "aggregateRating.starRating": 1, "docid": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_permissions(packages):
    if packages:
        docs = playstore_snapshot.find({"docid": {"$in": packages}}, {"_id": 0, "details.appDetails.permission": 1})
    else:
        docs = playstore_snapshot.find({}, {"_id": 0, "details.appDetails.permission": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_descriptions(packages):
    if packages:
        docs = playstore_detailed.find({"docid": {"$in": packages}}, {"_id": 0, "descriptionHtml": 1})
    else:
        docs = playstore_detailed.find({}, {"_id": 0, "descriptionHtml": 1, "translatedDescriptionHtml": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_package_by_permissions_size(size):
    docs = playstore_snapshot.find({"details.appDetails.permission": {"$size": size}}, {"docid": 1})
    return docs


@retry(pymongo.errors.AutoReconnect, tries=5, timeout_secs=1)
def get_edge_number():
    result = playstore_snapshot.aggregate([{'$group': {'_id': None, 'total': {'$sum': {'$size': '$similarTo'}}}}])
    command_result = result.next()
    print(command_result)
    return int(command_result.get('total'))
