# %%
import os
from typing import List

import crystal_toolkit  # noqa: F401
import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
from dash.dependencies import Input, Output
from dash_mp_components import Simple3DScene
from dscribe.descriptors import SOAP as SOAP_describe
from monty.json import jsanitize
from monty.serialization import loadfn
from pymatgen import Site
from pymatgen.analysis.graphs import StructureGraph, MoleculeGraph
from pymatgen.analysis.local_env import NearNeighbors
from pymatgen.core.structure import Molecule, Structure
from pymatgen.io.ase import AseAtomsAdaptor

dir_path = os.path.dirname(os.path.realpath(__file__))
DUMMY_SPECIES = "Si"

site_soap = SOAP_describe(
    species=[DUMMY_SPECIES],
    rcut=4,
    nmax=9,
    lmax=8,
    periodic=True,
    sparse=False,
)
adaptor = AseAtomsAdaptor()


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

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# App layout
app.layout = html.Div(
    [
        dcc.Input(id="mp-id", type="text", value="mp-14333", debounce=True),
        dcc.Input(id="n-random", type="number", value=50, debounce=True),
        dcc.RadioItems(
            id="site-index",
            value=0,
            labelStyle={'display': 'inline-block'}
        ),
        Simple3DScene(
            id='ref-site',
            sceneSize=400,
            settings={'extractAxis': True},
            axisView='SW',
            data={}
        ),
        html.Div(id="matched-site-plots", children=[]),
        html.Pre(id="debug-container", children=""),
        dcc.Store(id="selected-doc"),
        dcc.Store(id="random-site-collection"),
    ]
)


@app.callback(Output("selected-doc", "data"), [Input("mp-id", "value")])
def get_db_data(task_id):
    with soap_site_db as db:
        return jsanitize(db.query_one({'task_id': task_id}))


# @app.callback(Output("debug-container", "children"), [Input("random-site-collection", "data")])
# def get_debug(data):
#     return dumps(data, cls=MontyEncoder, indent=2)


@app.callback(Output("site-index", "options"), [Input("selected-doc", "data")])
def get_site_index(data):
    n_sites = len(data['site_data'])
    return [{'label': itr, 'value': itr} for itr in range(n_sites)]


@app.callback(Output("ref-site", "data"), [Input("selected-doc", "data"), Input("site-index", "value")])
def get_scene(data, site_index):
    site_data = data['site_data'][site_index]
    mol = Molecule.from_sites([Site.from_dict(isite)
                               for isite in site_data['local_graph']['sites']])
    scene = get_m_graph_from_mol(mol).get_scene()
    scene.name = "ref-site"
    return scene


@app.callback(Output("random-site-collection", "data"), [Input("n-random", "value")])
def get_random_sample(n_random):
    with soap_site_db as db:
        random_docs = [cc for cc in db._collection.aggregate([
            {"$sample": {"size": n_random}},
            {"$match": {"site_data": {"$exists": 1}}},
        ])]
        all_sites = []
        for r_doc in random_docs:
            for itr, isite in enumerate(r_doc['site_data']):
                all_sites.append({
                    'task_id': r_doc['task_id'],
                    'site_index': itr,
                    'local_graph': isite['local_graph'],
                    'soap_vec': isite['soap_vec']
                })
        return all_sites


@app.callback(Output("matched-site-plots", "children"),
              [Input("selected-doc", "data"), Input("site-index", "value"), Input("random-site-collection", "data"), ])
def get_closest_matched(ref_data, site_index, all_random_sites):
    """
    Find the 10 most similar sites
    Args:
        ref_data:
        site_index:
        all_random_sites:

    Returns:

    """
    ref_soap_vec = ref_data['site_data'][site_index]['soap_vec']

    def similarity(random_site_data):
        return np.abs(1 - np.dot(random_site_data, ref_soap_vec) / np.dot(ref_soap_vec, ref_soap_vec))

    all_sites_with_sim = [(isite, similarity(isite['soap_vec']))
                          for isite in all_random_sites]
    all_sites_with_sim.sort(key=lambda x: x[1])

    matched_res = []
    for itr, (site_info, proj) in enumerate(all_sites_with_sim[:3]):
        mol = Molecule.from_sites([Site.from_dict(isite)
                                   for isite in site_info['local_graph']['sites']])
        mg = get_m_graph_from_mol(mol)
        scene = mg.get_scene()
        scene.name = f"matched-site-{itr}"
        matched_res.append(site_info["task_id"] + "   " + f"{proj:0.4f}")
        matched_res.append(Simple3DScene(
            sceneSize=210,
            inletSize=150,
            inletPadding=0,
            axisView='SW',
            data=scene
        ))
    return matched_res


def get_m_graph_from_mol(mol):
    mg = MoleculeGraph.with_empty_graph(mol)
    for i in range(1, len(mg)):
        mg.add_edge(0, i)
    return mg

    # for sim_site in sorted(all_random_sites, key = similarity)[:10]:
    #     sim_sites_list.append((sim_site, ))


# @app.callback(Output("soap-results", "figure"), [Input("3d", "selectedObject")])
# def display_soap(selected_data):
#     """Show the soap sepectrum of a selected atom
#
#     Args:
#         selected_data ([type]): [description]
#
#     Returns:
#         [type]: [description]
#     """
#     if selected_data is None or len(selected_data) == 0:
#         return go.Figure()
#     n = int(selected_data[0]["id"].split("--")[-1])
#
#     soap_site_data = calculate_soap(structure, n)
#
#     fig = go.Figure(go.Bar(y=soap_site_data[:100]))
#     fig.update_layout(
#         autosize=False,
#         width=900,
#         height=300,
#         paper_bgcolor="LightSteelBlue",
#     )
#
#     return fig


def calculate_soap(structure: Structure, n: int):
    """
    Using a structure where all atoms have been converted to a dummy variable
    Calculate the soap vector at a particular site.

    Args:
        structure (Structure): The structure,  all atoms must be one type
        n (int): the site index of interest in the structure
    """
    ase_struct = adaptor.get_atoms(structure)
    return site_soap.create(ase_struct)[n]


def get_local_environment(
        structure: Structure, n: int, loc_env_strategy: NearNeighbors
) -> List[Molecule]:
    """Create the molecule object of the local environment
    based on a given local environment strategy

    Args:
        structure (Structure): Input structure
        n (int): The site index
        loc_env_strategy (NearNeighbors):

    Returns:
        Molecule: [description]
    """

    s_graph = StructureGraph.with_local_env_strategy(loc_env_strategy)
    return s_graph.get_subgraphs_as_molecules()


if __name__ == "__main__":
    app.run_server(debug=True)

# %%
