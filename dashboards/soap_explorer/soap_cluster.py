# %%
from typing import List
from monty.serialization import loadfn
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_mp_components import Simple3DScene
from pymatgen import Site
import crystal_toolkit  # noqa: F401
from pymatgen.analysis.graphs import MoleculeGraph
from pymatgen.core.structure import Molecule
import os
import pandas as pd
import plotly.express as px

dir_path = os.path.dirname(os.path.realpath(__file__))
DUMMY_SPECIES = "Si"

df_res = pd.read_pickle('df_res.pkl')
cluster_fig = fig = px.scatter(df_res, x="x", y='y', width=1000, height=900,
                               color='DBSCAN_lab', hover_name='index', title="Clusters of Similar Sites")

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]


def get_dbs(db_names: List[str], db_file: str = dir_path + "/./db_info.pub.json") -> List:
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


soap_site_db, = get_dbs(["soap_site_descriptors"])

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# App layout
app.layout = html.Div(
    [
        dcc.Graph(id="cluster-plot", figure=fig),
        html.Pre(id="debug", children=""),
        Simple3DScene(
            id='site',
            sceneSize=400,
            settings={'extractAxis': True},
            axisView='SW',
            data={}
        ),
    ]
)


@app.callback(Output('debug', 'children'), [Input('cluster-plot', 'clickData')])
def debug(data):
    if data is None:
        return 'NONE'
    return data["points"][0]["hovertext"]


@app.callback(Output('site', 'data'), [Input('cluster-plot', 'clickData')])
def get_sites_scene(data):
    if data is None:
        return {}
    task_id, n = data["points"][0]["hovertext"].split("+")
    with soap_site_db as db:
        doc = db.query_one({'task_id': task_id})
    scene = get_m_graph_from_site_data(doc['site_data'][int(n)]).get_scene()
    scene.name = "site"
    return scene


def get_m_graph_from_site_data(s_data):
    mol = Molecule.from_sites([Site.from_dict(isite)
                               for isite in s_data['local_graph']['sites']])
    mg = MoleculeGraph.with_empty_graph(mol)
    for i in range(1, len(mg)):
        mg.add_edge(0, i)
    return mg


if __name__ == "__main__":
    app.run_server(debug=True)

# %%
