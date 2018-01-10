# playstore_graph_analysis
Tools for the Analysis of the Google Play Store.

The focus of this software, is the analysis of a Google Play Store snapshot from two different points of view:

- as a collection of metadata, i.e. by computing statistics on downloads, ratings, price and so on (e.g. number of downloads distribution, average apps per developer...).
- as a graph of apps (Nodes) connected by relationships (Edges) like the similarity. If the app the app B is similar to the app A, i.e. the Play Store page of the app A lists the app B between the "Similar" applications, then there is a directed edge from A to B.

The Play Store dump format is a MongoDB database created by using [the dedicated Play Store crawler](https://github.com/alessandrodd/playstore_crawler).


## Requirements

- MongoDB 3.2+
- Python 2.7
- Modules in requirements.txt (use pip to install)
```
pip install -r requirements.txt
```

For technical details and for an overview of the Play Store snapshot linked later, check out [the project report (in Italian; sorry!)](https://goo.gl/R91t5e).

## Play Store Dump and Analysis

[Here you can find](https://goo.gl/gRBBz4) a snapshot of the Google Play Store taken in Aug/Sept 2017

To explore the collection, use the *mongorestore* command to import the collection in MongoDB, e.g.:

```
mongorestore --gzip --db mytestdb --collection playstore playstore_snapshot.bson.gz
```

[Here you can find](https://goo.gl/rCKjM3) a **list of all the application (app) packages**, in no particular order (*Warning: 80MB txt file*)

All the images and graphs used in the project report [are available here].