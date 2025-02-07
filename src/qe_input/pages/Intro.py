import os
import streamlit as st
import shutil
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from pymatgen.io.cif import CifWriter
from utils import list_of_pseudos, cutoff_limits
from data_utils import jarvis_structure_lookup, mp_structure_lookup, mc3d_structure_lookup, oqmd_strucutre_lookup
from kspacing_model import predict_kspacing

@st.fragment
def next_step():
    st.info('Next choose how to generate an input file:')
    col3, col4 = st.columns(2)

    with col3:
        if st.button("Chatbot generator"):
            st.switch_page("pages/Chatbot_generator.py")

    with col4:
        if st.button("Deterministic generator"):
            st.switch_page("pages/Deterministic_generator.py")

st.write("# Welcome to QE input generator! 👋")

st.markdown("""This app will help you generate input files for Quantum Espresso calculations.""")

st.sidebar.success("Provide specifications and select a way to generate input")

st.session_state['all_info']=False
structure=None

col1, col2 =st.columns(2)

with col1:
    functional_value = st.selectbox('XC-functional', 
                                ('PBE','PBEsol'), 
                                index=None, 
                                placeholder='PBE')
    
    mode_value = st.selectbox('pseudopotential flavour', 
                            ('efficiency','precision'), 
                            index=None, 
                            placeholder='efficiency')
    
with col2:
    kspacing_model = st.selectbox('ML model to predict kspacing', 
                            ('CGCNN'), 
                            index=None, 
                            placeholder='CGCNN')
    

if functional_value:
    st.session_state['functional'] = functional_value
else:
    st.session_state['functional'] = 'PBE'

if mode_value:
    st.session_state['mode'] = mode_value
else:
    st.session_state['mode'] = 'efficiency'

if kspacing_model:
    st.session_state['kspacing_model'] = kspacing_model
else:
    st.session_state['kspacing_model'] = 'CGCNN'


# upload structure file into buffer
tab1, tab2 = st.tabs(["Upload structure", "Search for structure"])

with tab1:
    structure_file = st.file_uploader("Upload the structure file", type=("cif"))

with tab2:
    input_formula = st.text_input("Chemical formula (try to find structure in free databases)")

if not structure_file and not input_formula:
    st.info("Please add your structure file or chemical formula to continue")
elif input_formula:
    composition=Composition(input_formula)
    formula,_=composition.get_reduced_formula_and_factor()
    # may also include alexandria https://alexandria.icams.rub.de/
    structure_database = st.radio(label='Choose the database to search for the structure',
                                  options=['Jarvis','MP', 'MC3D', 'OQMD'],
                                  horizontal=True,
                                  )
    if structure_database=='Jarvis':
        try:
            result=jarvis_structure_lookup(formula,id=False)
            selected_row=st.data_editor(
                            result,
                            column_config={
                                "select": st.column_config.CheckboxColumn(
                                    "Which structure?",
                                    help="Select your structure",
                                    default=False,
                                )
                            },
                            disabled=["formula",'energy','sg','natoms','abc','angles'],
                            hide_index=True,
                        )
            if(len(selected_row.loc[selected_row['select']==True])==1):
                x=selected_row.loc[selected_row['select']==True]['id'].values[0]
            elif(len(selected_row.loc[selected_row['select']==True])==0):
                st.info('Choose the structure!')
            else:
                st.info('You need to choose one structure!')
            if x is not None:
                structure=jarvis_structure_lookup(formula,id=x)
                unit_cell = st.selectbox('Transform unit cell', 
                            ('leave as is','niggli reduced cell', 'primitive','supercell'), 
                            index=None, 
                            placeholder='leave as is')
                if(unit_cell=='niggli reduced cell'):
                    structure=structure.get_reduced_structure()
                elif(unit_cell=='primitive'):
                    structure=structure.get_primitive_structure()
                elif(unit_cell=='supercell'):
                    multi=st.text_input(label='multiplication factor in the format (na,nb,nc)',
                                        placeholder='(2,2,2)')
                    multi=tuple(multi[1:-1].split(','))
                    structure.make_supercell(multi)
                    st.info('Supercell is created')

        except Exception as exc:
            st.info('Structure was not found!')
            st.info(exc)

    elif structure_database=='MP':
        mp_api_key = st.text_input("Materials Project API Key ([Get a MP API key](https://next-gen.materialsproject.org/api#api-key))", key="mp_api_key", type="password")
        if mp_api_key:
            try:
                structure=mp_structure_lookup(formula,mp_api_key)
                st.info('Structure was found in Materials Project database')
            except:
                st.info('Structure was not found!')
    elif structure_database=='MC3D':
        try:
            structure=mc3d_structure_lookup(formula)
            st.info('Structure was found in MC3D dataset')
        except Exception as exc:
            st.info('Structure was not found!')
            st.info(exc)
    elif structure_database=='OQMD':
        try:
            structure=oqmd_strucutre_lookup(formula)
            st.info('Structure was found in OQMD database')
        except Exception as exc:
            st.info('Structure was not found!')
            st.info(exc)
elif structure_file:
    save_directory = "./src/qe_input/temp/"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)
    file_path = os.path.join(save_directory, 'structure.cif')
    with open(file_path, "wb") as f:
        f.write(structure_file.getbuffer())
    structure = Structure.from_file(file_path)

if structure:
    save_directory = "./src/qe_input/temp/"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)
    file_path = os.path.join(save_directory, 'structure.cif')
    write_cif=CifWriter(structure)
    write_cif.write_file(file_path)
    st.session_state['save_directory']=save_directory
    st.session_state['structure_file']=file_path
    st.session_state['structure']=structure

    composition = Composition(structure.alphabetical_formula)
    st.session_state['composition']=structure.alphabetical_formula
    pseudo_path="./src/qe_input/pseudos/"
    pseudo_family, list_of_element_files=list_of_pseudos(pseudo_path, st.session_state['functional'], 
                                                         st.session_state['mode'], composition,st.session_state['save_directory'])
    st.session_state['pseudo_family']=pseudo_family
    st.session_state['list_of_element_files']=list_of_element_files
    st.session_state['pseudo_path']=pseudo_path

    cutoffs=cutoff_limits('./src/qe_input/pseudo_cutoffs/', st.session_state['functional'],
                          st.session_state['mode'], composition)
    st.session_state['cutoffs']=cutoffs

    if(st.session_state['kspacing_model']=='CGCNN'):
        kspacing=predict_kspacing(structure)

    st.session_state['kspacing']=kspacing
    st.session_state['all_info']=True
    
    next_step()