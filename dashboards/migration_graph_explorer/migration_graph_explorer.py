# %%
from collections import defaultdict
from typing import List, Union
from monty.serialization import loadfn
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go


def get_dbs(db_names: List[str], db_file: str = "./db_info.pub.json") -> List:
    """Read the db_file and get the databases corresponding to <<db_name>>

    Args:
        db_name (List[str]): A list of names of the database we want
        db_file (str): The db_file we are reading from

    Returns:
        MongograntStore: the store we need to access
    """
    db_dict = loadfn(db_file)
    stores = []
    for j_name in db_names:
        if j_name not in db_dict:
            raise ValueError(
                f"The store named {j_name} is missing from the db_file")
        stores.append(db_dict[j_name])
    return stores


migration_db, descriptor_db = get_dbs(
    ["migration_graphs", "migration_graphs_descriptor"]
)

with descriptor_db as db:
    all_ids = descriptor_db.distinct(db.key)

all_ids_options = [{"label": _, "value": _} for _ in all_ids]

# %%
# recursive defualtdict


def rec_dd():
    return defaultdict(rec_dd)


res_dict = rec_dd()
with descriptor_db as db:
    for cc in db.query():
        try:
            condensed_structure = cc["migration_graph"]["condensed_structure"]
        except Exception:
            continue
        if not condensed_structure:
            continue

        dim = condensed_structure["dimensionality"]
        sys = condensed_structure["crystal_system"]
        m_type = condensed_structure["mineral"]["type"]
        res_dict[f"D-{dim}"][sys][m_type][cc["snl_id"]] = 1
sunburst_data = []

level_data = {}


def recurse_fill(d, full_id=""):
    if isinstance(d, int):
        a, b, c, d = full_id.split(".")
        level_data[d] = ".".join([a, b, c])
        return 1
    tot = 0
    for k, v in d.items():
        if len(full_id) == 0:
            new_key = f"{k}"
        else:
            new_key = f"{full_id}.{k}"
        sub_tot = recurse_fill(v, full_id=new_key)
        sunburst_data.append(
            {"id": new_key, "parent": full_id, "val": sub_tot})
        tot += sub_tot
    return tot


# Run the
recurse_fill(res_dict)

sb_ids = []
sb_labs = []
sb_parents = []
sb_values = []

for cc in sunburst_data:
    sb_ids.append(cc["id"])
    lab = cc["id"].split(".")[-1]
    sb_labs.append(lab)
    sb_parents.append(cc["parent"])
    sb_values.append(cc["val"])


# %%
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# App layout
app.layout = html.Div(
    [
        dcc.Graph(id="sun-plot", style={"height": 1000}),
        dcc.Dropdown(id="id-select", options=all_ids_options, value=""),
    ]
)


# Graph
@app.callback(Output("sun-plot", "figure"), [Input("id-select", "value")])
def update_figure(selected_id: Union[str, int]):
    """Redraw the sunburst figure zoomed in on the selected material

    Args:
        selected_id (Union[str, int]): the id of the selected material
    """
    if selected_id == "":
        lvl = None
    else:
        lvl = level_data[selected_id]

    fig = go.Figure(
        go.Sunburst(
            ids=sb_ids,
            labels=sb_labs,
            parents=sb_parents,
            values=sb_values,
            level=lvl,
        )
    )

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
