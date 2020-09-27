# %%
from typing import List
from monty.serialization import loadfn
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from dash_mp_components import Simple3DScene
from pymatgen import MPRester
import crystal_toolkit  # noqa: F401
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.core.structure import Molecule, Structure
from dscribe.descriptors import SOAP as SOAP_describe
from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.analysis.local_env import NearNeighbors


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

# %%


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

structure = MPRester().get_structure_by_material_id("mp-149")
structure.get_primitive_structure()
structure.insert(0, "Si", [0.15, 0.75, 0.5])

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
        # html.Pre(id="debug-container", children=""),
        # html.Pre(id="soap-results", children=""),
        dcc.Graph(id="soap-results", style={"height": 1234}, figure=None),
    ]
)


# @app.callback(Output("debug-container", "children"), [Input("3d", "selectedObject")])
# def show_selected(value):
#     return json.dumps(value, indent=2)


@app.callback(Output("soap-results", "figure"), [Input("3d", "selectedObject")])
def display_soap(selected_data):
    """Show the soap sepectrum of a selected atom

    Args:
        selected_data ([type]): [description]

    Returns:
        [type]: [description]
    """
    if selected_data is None or len(selected_data) == 0:
        return go.Figure()
    n = int(selected_data[0]["id"].split("--")[-1])

    soap_site_data = calculate_soap(structure, n)

    fig = go.Figure(go.Bar(y=soap_site_data[:100]))
    fig.update_layout(
        autosize=False,
        width=900,
        height=300,
        paper_bgcolor="LightSteelBlue",
    )

    return fig


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
