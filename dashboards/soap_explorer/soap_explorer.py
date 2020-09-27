# %%
import json
from typing import List
from monty.serialization import loadfn
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# import plotly.graph_objects as go
from dash_mp_components import Simple3DScene
from pymatgen import MPRester
import crystal_toolkit   # noqa: F401


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


# soap_db, snls_db = get_dbs(["soap_descriptors", "snls_icsd"])


external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

structure = MPRester().get_structure_by_material_id("Si")

# App layout
app.layout = html.Div(
    [
        dcc.Input(id="input2", type="text", placeholder="", debounce=True),
        Simple3DScene(
            id="3d",
            sceneSize=800,
            inletSize=150,
            settings={"extractAxis": True},
            inletPadding=0,
            data=structure.get_scene(),
        ),
        html.Pre(id='debug-container', children=''),
    ]
)


@app.callback(Output('debug-container', 'children'),
              [Input('3d', 'selectedObject')])
def show_selected(value):
    # do something a bit more complex
    return json.dumps(value, indent=2)


@app.callback(Output('debug-container', 'children'),
              [Input('3d', 'selectedObject')])
def calculate_soap(selected_data):
    # do something a bit more complex
    return json.dumps(selected_data, indent=2)


if __name__ == "__main__":
    app.run_server(debug=True)
