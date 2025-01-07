import sys
import os
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/qe_input')))

from streamlit.testing.v1 import AppTest
from dotenv import load_dotenv
from openai import OpenAI
import os
import pytest
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
import streamlit as st
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

CIF="""# generated using pymatgen
data_CoF2
_symmetry_space_group_name_H-M   'P 1'
_cell_length_a   4.64351941
_cell_length_b   4.64351941
_cell_length_c   3.19916469
_cell_angle_alpha   90.00000000
_cell_angle_beta   90.00000000
_cell_angle_gamma   90.00000000
_symmetry_Int_Tables_number   1
_chemical_formula_structural   CoF2
_chemical_formula_sum   'Co2 F4'
_cell_volume   68.98126085
_cell_formula_units_Z   2
loop_
 _symmetry_equiv_pos_site_id
 _symmetry_equiv_pos_as_xyz
  1  'x, y, z'
loop_
 _atom_type_symbol
 _atom_type_oxidation_number
  Co2+  2.0
  F-  -1.0
loop_
 _atom_site_type_symbol
 _atom_site_label
 _atom_site_symmetry_multiplicity
 _atom_site_fract_x
 _atom_site_fract_y
 _atom_site_fract_z
 _atom_site_occupancy
  Co2+  Co0  1  0.00000000  0.00000000  0.00000000  1
  Co2+  Co1  1  0.50000000  0.50000000  0.50000000  1
  F-  F2  1  0.30433674  0.30433674  0.00000000  1
  F-  F3  1  0.69566326  0.69566326  0.00000000  1
  F-  F4  1  0.80433674  0.19566326  0.50000000  1
  F-  F5  1  0.19566326  0.80433674  0.50000000  1"""

# check that we can run the app and it has all nessecary components
def test_app():
    at = AppTest(script_path="src/qe_input/QE_input_generation_app.py", default_timeout=10)
    at.run()
    assert not at.exception
    # Sidebar elements
    sidebar_input_text_labels=[x.label for x in at.sidebar.get('text_input')]
    assert 'OpenAI API Key' in sidebar_input_text_labels
    for x in at.sidebar.get('text_input'):
        if(x.label=='OpenAI API Key'):
            assert x.key == 'feedback_api_key'
    sidebar_selectbox_labels=[x.label for x in at.sidebar.get('selectbox')]
    assert 'XC-functional' in sidebar_selectbox_labels
    assert 'pseudopotential flavour' in sidebar_selectbox_labels
    assert 'assistant LLM' in sidebar_selectbox_labels
    for x in at.sidebar.get('selectbox'):
        if(x.label=='XC-functional'):
            assert 'PBE' in x.options
            assert 'PBEsol' in x.options
        if(x.label=='pseudopotential flavour'):
            assert 'efficiency' in x.options
            assert 'precision' in x.options
        if(x.label=='assistant LLM'):
            assert 'gpt-4o' in x.options
            assert 'gpt-4o-mini' in x.options
            assert 'gpt-3.5-turbo' in x.options
    # Main body elements. Note that fileupload is recordered as 'UnknownElement' and 
    # neither is recognised by the test class, nor can be interacted with...
    

# check that fake cif file is read correctely and save correctly in the container
def test_structure_read(tmp_path):
    mock_file = tmp_path / 'mock_structure.cif'
    mock_file.write_text(CIF, encoding="utf-8")
    assert Structure.from_file(mock_file)
    assert Structure.from_file(mock_file).lattice
    assert Structure.from_file(mock_file).formula
    
    with pytest.raises(ValueError):
        mock_file = tmp_path / 'mock_structure.cif'
        mock_file.write_text(CIF[-10], encoding="utf-8")
        assert Structure.from_file(mock_file)



