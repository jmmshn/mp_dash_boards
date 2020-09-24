# Plotly Dashboards for personal MP workflows

Usage each app will access data via MongoGrantStores serialized in a `db_info.pub.json` file.

The file contains a dictionary of variable names and the MongoGrantStore they correspond to.

```
{
    "db_in1" : ...JSON dump of MongoGrantStore...,
    "db_in2" : ...JSON dump of MongoGrantStore...,
}
```
