# Plotly Dashboards for personal MP workflows

Usage each app will access data via then `MongograntStore`'s serialized in a `db_info.pub.json` file.

The file contains a dictionary of variable names and the `MongograntStore`'s they correspond to.

```
{
    "db_in1" : ...JSON dump of MongograntStore...,
    "db_in2" : ...JSON dump of MongograntStore...,
}
```

Each app needs a `get_db` function which just returns a list of stores that the user needs to connect to
Use the following as an example.

```python
def get_dbs(db_names: List[str], db_file: str = "./db_info.pub.json") -> List:
    """Read the db_file and get the databases corresponding to <<db_name>>

    Args:
        db_name (List[str]): A list of names of the database we want
        db_file (str): The db_file we are reading from

    Returns:
        List[MongograntStore]: the store we need to access
    """
    db_dict = loadfn(db_file)
    stores = []
    for j_name in db_names:
        if j_name not in db_dict:
            raise ValueError(
                f"The store named {j_name} is missing from the db_file")
        stores.append(db_dict[j_name])
    return stores
```

Note, all of the data stored in the json file is from `MongograntStore` which should not contain any actually login information, it should only contain your aliases.
You can use an additional `db_info.priv.json` if you wantto be extra careful, or if your insist on using `MongoStores` instead.
