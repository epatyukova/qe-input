import os
import streamlit as st
import pandas as pd
from openai import OpenAI
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from pymatgen.io.cif import CifWriter
from utils import list_of_pseudos, cutoff_limits, generate_input_file
from data_utils import jarvis_structure_lookup, mp_structure_lookup, mc3d_structure_lookup, oqmd_strucutre_lookup
from kspacing_model import predict_kspacing

import shutil
import json
import time

st.title("Generate QE input with a deterministic function")

if 'all_info' not in st.session_state.keys():
    st.session_state['all_info']=False

if not (st.session_state['all_info']):
    st.info("Please provide all necessary material information on the Intro page")

if st.session_state['all_info']:
    if st.button("Generate QE input"):
        input_file_content=generate_input_file(st.session_state['save_directory'], 
                                            st.session_state['structure_file'], 
                                            './', 
                                            st.session_state['list_of_element_files'], 
                                            st.session_state['cutoffs']['max_ecutwfc'], 
                                            st.session_state['cutoffs']['max_ecutrho'], 
                                            kspacing=st.session_state['kspacing'])
        if input_file_content:
            st.session_state['input_file'] = input_file_content
            st.session_state['input_file_path'] = './src/qe_input/temp/qe.in'
        else:
            st.write('Error: Input file was not generated!')
        shutil.make_archive('./src/qe_input/qe_input', 'zip','./src/qe_input/temp')

        st.write('compound: ', st.session_state['composition'])
        st.write('Pseudo family used: ', st.session_state['pseudo_family'])
        st.write('energy cutoff (Ry): ', st.session_state['cutoffs']['max_ecutwfc'])
        st.write('density cutoff (Ry): ', st.session_state['cutoffs']['max_ecutrho'])
        st.write('k spacing (1/A): ', st.session_state['kspacing'])

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

# if not openai_api_key:
#     st.info("Please add your OpenAI API key to continue.", icon="🗝️")
# if openai_api_key:
#     # Create an OpenAI client.
#     client = OpenAI(api_key=openai_api_key)
#     st.markdown('**You can ask agent to correct any input parameters, ask about their meaning, or generate aiida code to run calculations!**')
#     # Create a session state variable to store the chat messages. This ensures that the
#     # messages persist across reruns.
#     if "messages" not in st.session_state:
#         st.session_state.messages = []
    
#     # add input file content to the prompt
#     if 'input_file' in st.session_state.keys() and 'input_file_path' in st.session_state.keys():
#         st.session_state.messages.append({"role": "system", "content": "When generating reply take into account QE input file content:\n"\
#                                             + st.session_state['input_file']+\
#                                             'and its locaiton: ' + st.session_state['input_file_path']})
#     # Display the existing chat messages via `st.chat_message`.
#     for message in st.session_state.messages:
#         if(message["role"]=="user" or message["role"]=="assistant"):
#             st.markdown(message["content"])
    
#     # Create a chat input field to allow the user to enter a message. This will display
#     # automatically at the bottom of the page.
#     if prompt := st.chat_input("Do you have any questions?"):

#         # Store and display the current prompt.
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)
        
#         # Generate a response using the OpenAI API.
#         stream = client.chat.completions.create(
#             model=st.session_state['llm_name'],
#             messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
#             stream=True,
#         )

#         # Stream the response to the chat using `st.write_stream`, then store it in 
#         # session state.
#         with st.chat_message("assistant"):
#             response = st.write_stream(stream)
#         st.session_state.messages.append({"role": "assistant", "content": response})