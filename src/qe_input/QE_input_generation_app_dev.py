import os
import streamlit as st
import pandas as pd
from openai import OpenAI
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from pymatgen.io.cif import CifWriter
from utils import list_of_pseudos, cutoff_limits, generate_input_file
from data_utils import jarvis_structure_lookup, mp_structure_lookup, mc3d_structure_lookup, oqmd_strucutre_lookup

import shutil
import json
import time

structure = None

with st.sidebar:
    functional_value = st.selectbox('XC-functional', 
                              ('PBE','PBEsol'), 
                              index=None, 
                              placeholder='PBE')
    mode_value = st.selectbox('pseudopotential flavour', 
                        ('efficiency','precision'), 
                        index=None, 
                        placeholder='efficiency')
    
    openai_api_key = st.text_input("OpenAI API Key ([Get an OpenAI API key](https://platform.openai.com/account/api-keys))", 
                                   key="feedback_api_key", 
                                   type="password",
                                   )
    llm_name_value = st.selectbox('assistant LLM', 
                        ("gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo'), 
                        index=None, 
                        placeholder='gpt-4o')

if functional_value:
    st.session_state['functional'] = functional_value
else:
    st.session_state['functional'] = 'PBE'

if mode_value:
    st.session_state['mode'] = mode_value
else:
    st.session_state['mode'] = 'efficiency'

if llm_name_value:
    st.session_state['llm_name'] = llm_name_value
else:
    st.session_state['llm_name'] = 'gpt-4o'


# Show title and description.
st.title("💬 Chatbot for QE input")

st.write(
    """To generate input file, provide structure CIF file.
    The app will generate an input file for QE single point scf calculations and Chatbot can answer your questions."""
)

# upload structure file into buffer
tab1, tab2 = st.tabs(["Upload structure", "Search for structure"])

with tab1:
    structure_file = st.file_uploader("Upload the structure file", type=("cif"))

with tab2:
    input_formula = st.text_input("Chemical formula (try to find structure in free databases)")

###############################################
### Generating QE input from structure file ###
###############################################

if not structure_file and not input_formula:
    st.info("Please add your structure file or chemical formula to continue")
elif input_formula:
    # if not mp_api_key:
    #     st.info("Please add your MP API key to check Materials Project database for the structure.", icon="🗝️")
    # else:
    composition=Composition(input_formula)
    formula,_=composition.get_reduced_formula_and_factor()
    # may also include alexandria https://alexandria.icams.rub.de/
    structure_database = st.radio(label='Choose the database to search for the structure',
                                  options=['Jarvis','MP', 'MC3D', 'OQMD'],
                                  horizontal=True,
                                  )
    if structure_database=='Jarvis':
        try:
            structure=jarvis_structure_lookup(formula)
            st.info('Structure was found in Jarvis 3d_dft dataset')
        except:
            st.info('Structure was not found!')
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
            # st.info(exc)
    elif structure_database=='OQMD':
        try:
            structure=oqmd_strucutre_lookup(formula)
            st.info('Structure was found in OQMD database')
        except Exception as exc:
            st.info('Structure was not found!')
            # st.info(exc)
    

elif structure_file:
    save_directory = "./src/qe_input/temp/"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)
    file_name='structure.cif'
    file_path = os.path.join(save_directory, file_name)
    with open(file_path, "wb") as f:
        f.write(structure_file.getbuffer())
    structure = Structure.from_file(file_path)

if structure:
    save_directory = "./src/qe_input/temp/"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)
    file_name='structure.cif'
    file_path = os.path.join(save_directory, file_name)
    st.session_state['save_directory']=save_directory
    st.session_state['structure_file']=file_path
    write_cif=CifWriter(structure)
    write_cif.write_file(file_path)

    composition = Composition(structure.alphabetical_formula)
    pseudo_path="./src/qe_input/pseudos/"
    if not os.path.exists(pseudo_path):
        os.makedirs(pseudo_path)

    pseudo_family, list_of_element_files=list_of_pseudos(pseudo_path, st.session_state['functional'], 
                                                         st.session_state['mode'], composition,save_directory)
    cutoffs=cutoff_limits('./src/qe_input/pseudo_cutoffs/', st.session_state['functional'],
                          st.session_state['mode'], composition)
    
    input_file_content=generate_input_file(save_directory, 
                                           file_path, 
                                           './', 
                                           list_of_element_files, 
                                           cutoffs['max_ecutwfc'], 
                                           cutoffs['max_ecutrho'], 
                                           kspacing=0.01)
    if input_file_content:
        st.session_state['input_file'] = input_file_content
        st.session_state['input_file_path'] = './src/qe_input/temp/qe.in'
    else:
        st.write('Error: Input file was not generated!')
    shutil.make_archive('./src/qe_input/qe_input', 'zip','./src/qe_input/temp')

    st.write('compound: ', composition)
    st.write('Pseudo family used: ', pseudo_family)
    st.write('energy cutoff (Ry): ', cutoffs['max_ecutwfc'])
    st.write('density cutoff (Ry): ', cutoffs['max_ecutrho'])
    st.write('k spacing (1/A): ', 0.023)

    st.download_button(
            label="Download the files",
            data=open('./src/qe_input/qe_input.zip', "rb").read(),
            file_name='qe_input.zip',
            mime="application/octet-stream"
        )
    
    # visualising the structure and printing info about the parameters

    # server=Flask(__name__)
    # app = Dash(__name__,server=server)
    # app = Dash()
    # structure_component = StructureMoleculeComponent(structure, id="structure")
    # app.layout=html.Div([structure_component.layout()])
    # def run_dash_app():
    #     app.run_server(debug=False, host="0.0.0.0", port=8055)

    # thread = threading.Thread(target=run_dash_app, daemon=True)
    # thread.start()
    # time.sleep(3)
    # st.components.v1.iframe(src="http://0.0.0.0:8055", height=600)
    
    # server=Flask(__name__)
    # app = Dash(__name__,server=server)
    # # app = Dash()
    # structure_component = StructureMoleculeComponent(structure, id="structure")
    # app.layout=html.Div([html.Button('Draw the structure', id='button-draw-structure',n_clicks=0),
    #                      html.Div(children=structure_component.layout(),id='layout'),
    #                     ])
    # @callback(
    #     Output(component_id='layout', component_property='children'),
    #     Input(component_id='button-draw-structure', component_property='n_clicks'), Input(component_property='structure')
    # )
    # def update_layout(n_clicks,structure):
    #     print(n_clicks)
    #     structure_component = StructureMoleculeComponent(structure, id="structure")
    #     time.sleep(2)
    #     return structure_component.layout()

    # # # # now put dash app inside streamlit container
    # def run_dash_app():
    #     return app.run_server(debug=False, host="0.0.0.0", port=8055)
    # thread = threading.Thread(target=run_dash_app, daemon=True)
    # thread.start()
    # time.sleep(3)
    # st.components.v1.iframe(src="http://0.0.0.0:8055", height=100)

    

###############################################
### LLM part to answer questions            ###
###############################################

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
if openai_api_key:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)
    st.markdown('**You can ask agent to correct any input parameters, ask about their meaning, or generate aiida code to run calculations!**')
    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # add input file content to the prompt
    if 'input_file' in st.session_state.keys() and 'input_file_path' in st.session_state.keys():
        st.session_state.messages.append({"role": "system", "content": "When generating reply take into account QE input file content:\n"\
                                            + st.session_state['input_file']+\
                                            'and its locaiton: ' + st.session_state['input_file_path']})
    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        if(message["role"]=="user" or message["role"]=="assistant"):
            st.markdown(message["content"])
    
    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("Do you have any questions?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate a response using the OpenAI API.
        stream = client.chat.completions.create(
            model=st.session_state['llm_name'],
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})