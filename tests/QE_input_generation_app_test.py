import sys
import os
import shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/qe_input')))

from streamlit.testing.v1 import AppTest
from dotenv import load_dotenv
from openai import OpenAI
import re
import pytest
import json
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
import streamlit as st

from unittest.mock import MagicMock
from streamlit.runtime.memory_uploaded_file_manager import MemoryUploadedFileManager, UploadedFileRec
from streamlit.testing.v1.local_script_runner import LocalScriptRunner
from streamlit.runtime.state.session_state import SessionState
from streamlit.runtime.state.safe_session_state import SafeSessionState
from streamlit.runtime.pages_manager import PagesManager
from streamlit.runtime import Runtime

from streamlit.runtime.fragment import MemoryFragmentStorage
from streamlit.runtime.scriptrunner import RerunData, ScriptRunner, ScriptRunnerEvent
from streamlit.runtime.scriptrunner.script_cache import ScriptCache
import uuid
from time import sleep

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

ELEMENTS=['Ac', 'Ag', 'Al', 'Am', 'Ar', 'As', 'At', 'Au', 'B', 'Ba', 'Be',\
       'Bi', 'Bk', 'Br', 'C', 'Ca', 'Cd', 'Ce', 'Cf', 'Cl', 'Cm', 'Co',\
       'Cr', 'Cs', 'Cu', 'Dy', 'Er', 'Es', 'Eu', 'F', 'Fe', 'Fm', 'Fr',\
       'Ga', 'Gd', 'Ge', 'H', 'He', 'Hf', 'Hg', 'Ho', 'I', 'In', 'Ir',\
       'K', 'Kr', 'La', 'Li', 'Lr', 'Lu', 'Md', 'Mg', 'Mn', 'Mo', 'N',\
       'Na', 'Nb', 'Nd', 'Ne', 'Ni', 'No', 'Np', 'O', 'Os', 'P', 'Pa',\
       'Pb', 'Pd', 'Pm', 'Po', 'Pr', 'Pt', 'Pu', 'Ra', 'Rb', 'Re', 'Rh',\
       'Rn', 'Ru', 'S', 'Sb', 'Sc', 'Se', 'Si', 'Sm', 'Sn', 'Sr', 'Ta',\
       'Tb', 'Tc', 'Te', 'Th', 'Ti', 'Tl', 'Tm', 'U', 'V', 'W', 'Xe', 'Y',\
       'Yb', 'Zn', 'Zr']

# check that we can run the app and it has all necessary components
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
            x._value='PBEsol'
            x.run()
            assert at.session_state['functional']=='PBEsol'
        if(x.label=='pseudopotential flavour'):
            assert 'efficiency' in x.options
            assert 'precision' in x.options
            x._value='precision'
            x.run()
            assert at.session_state['mode']=='precision'
        if(x.label=='assistant LLM'):
            assert 'gpt-4o' in x.options
            assert 'gpt-4o-mini' in x.options
            assert 'gpt-3.5-turbo' in x.options
            x._value='gpt-3.5-turbo'
            x.run()
            assert at.session_state['llm_name']=='gpt-3.5-turbo'
    # Main body elements. Note that fileupload is recordered as 'UnknownElement' and 
    # neither is recognised by the test class, nor can be interacted with...
    main_values=[at.main[i].value for i in range(len(at.main))]
    # not very useful assertion about whether any headings/sentences/info in the main
    # section contain 'structure file' string
    assert any([re.search('structure file',main_values[i]) is not None \
                for i in range(len(main_values)) if isinstance(main_values[i],str)])
    assert at.get('chat_input')==[]
    # Check that the chat_input appears after the openai_api_key input
    at.sidebar.get('text_input')[0]._value=openai_api_key
    at.run()
    assert at.session_state['feedback_api_key'] == openai_api_key
    assert at.get('chat_input')!=[]
    assert at.session_state['messages']==[]
    # Testing interaction with the agent
    at.get('chat_input')[0].set_value('Hello')
    at.get('chat_input')[0].run()
    assert at.session_state['messages']!=[] 
    assert at.session_state['messages'][0]['role']=='user'
    assert at.session_state['messages'][1]['role']=='assistant'

# check that fake cif file is read correctely and save correctly in the container
def test_structure_read(tmp_path):
    mock_file = tmp_path / 'mock_structure.cif'
    mock_file.write_text(CIF, encoding="utf-8")
    assert Structure.from_file(mock_file)
    assert Structure.from_file(mock_file).lattice
    assert Structure.from_file(mock_file).formula
    # try to open corrupted cif
    with pytest.raises(ValueError):
        mock_file = tmp_path / 'mock_structure.cif'
        mock_file.write_text(CIF[-10], encoding="utf-8")
        assert Structure.from_file(mock_file)

# check that pseudos for all elements exist
def test_pseudos():
    assert os.path.exists('./src/qe_input/pseudos/')
    assert os.path.exists('./src/qe_input/pseudo_cutoffs/')
    list_of_pseudo_types=os.listdir('./src/qe_input/pseudos/')
    list_of_pseudo_types.remove(".DS_Store")
    list_of_cutoffs=os.listdir('./src/qe_input/pseudo_cutoffs/')
    list_of_cutoffs.remove(".DS_Store")
    ## check taht for each combination of functional and mode there is a folder
    ## that each folder contains psudos for all elements
    at = AppTest(script_path="src/qe_input/QE_input_generation_app.py", default_timeout=10)
    at.run()
    for x in at.sidebar.get('selectbox'):
        if(x.label=='XC-functional'):
            functional_options=x.options
        if(x.label=='pseudopotential flavour'):
            mode_options=x.options
    for functional in functional_options:
        for mode in mode_options:
            switch_pseudo=0
            switch_cutoff=0
            for pseudo in list_of_pseudo_types:
                if(functional in pseudo and mode in pseudo):
                    switch_pseudo=1
            for cutoff_name in list_of_cutoffs:
                if(functional in pseudo and mode in cutoff_name):
                    switch_cutoff=1
            assert switch_pseudo # it would be good to add a message about what functional/mode combination fail
            assert switch_cutoff
    for folder in list_of_pseudo_types:
        list_of_files=os.listdir('./src/qe_input/pseudos/'+folder)
        represented_elements=[]
        for file in list_of_files:
            if(file[1]=='.' or file[1]=='_' or file[1]=='-'):
                el=file[0]
                el=el.upper()
            elif(file[2]=='.' or file[2]=='_' or file[2]=='-'):
                el=file[:2]
                el=el[0].upper()+el[1].lower()
            assert el in ELEMENTS
            represented_elements.append(el)
        for el in ELEMENTS:
            assert el in represented_elements
    for file in list_of_cutoffs:
        with open('./src/qe_input/pseudo_cutoffs/'+file,'r') as f:
            cutoffs=json.load(f)
            for el in ELEMENTS:
                assert el in cutoffs.keys()
    
# it is not clear how to test file uploader/downloader
# the code below essentially is not working, the 'uploaded' mock file is not seen
# Probably it is better to modify AppTest class to include self.upload_file_manager,
# its interaction with events/session_state and a method reacting to changes in the list of uploaded files

# def test_upload_with_scriptrunner(tmp_path):
#     # Initialize dependencies for ScriptRunner 

#     session_id = str(uuid.uuid4())

#     # Initialize MemoryUploadedFileManager
#     mock_file = tmp_path / "mock_structure.cif"
#     mock_file.write_text(CIF, encoding="utf-8")

#     # Set up the script path and ScriptRunner
#     app_script_path = "src/qe_input/QE_input_generation_app.py"  # Replace with the path to your Streamlit app
#     # session_state = SafeSessionState(SessionState(), lambda: None)
#     # pages_manager=PagesManager(main_script_path=app_script_path)
#     # uploaded_file_mgr = MemoryUploadedFileManager(tmp_path)

#     script_runner = LocalScriptRunner(
#             script_path=app_script_path,
#             session_state=SafeSessionState(SessionState(), lambda: None),
#             pages_manager=PagesManager(main_script_path=app_script_path),
#             args=None,
#             kwargs=None
#         )

#     # Start the ScriptRunner
#     script_runner.start()
#     print(script_runner.session_state)
#      # Add a file to UploadedFileManager
#     file_id = "test_file_id"
#     uploaded_file_mgr = MemoryUploadedFileManager(tmp_path)
#     script_runner.uploaded_file_mgr = uploaded_file_mgr
#     Runtime._instance = script_runner

#     uploaded_file_rec = UploadedFileRec(
#         file_id=file_id,
#         name="mock_structure.cif",
#         type="text/plain",
#         data=mock_file.read_bytes(),
#     )
#     script_runner.uploaded_file_mgr.add_file(session_id, uploaded_file_rec)
#     sleep(3)
#         # Validate uploaded file behavior
#     files = script_runner.uploaded_file_mgr.get_files(session_id, file_id)
#     print("Files in manager:", files) 
#     assert files
