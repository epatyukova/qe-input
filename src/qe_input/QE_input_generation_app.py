import os
import streamlit as st
import pandas as pd
from openai import OpenAI
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from utils import list_of_pseudos, cutoff_limits, generate_input_file

from crystal_toolkit.components.structure import StructureMoleculeComponent
import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS
import dash

from dash import html, Dash, callback, Output, Input
from flask import Flask

import threading

import shutil
import json
import time

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="feedback_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    functional_value = st.selectbox('XC-functional', 
                              ('PBE','PBEsol'), 
                              index=None, 
                              placeholder='PBE')
    mode_value = st.selectbox('pseudopotential flavour', 
                        ('efficiency','precision'), 
                        index=None, 
                        placeholder='efficiency')
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
    The Chatbot will generate an input file for QE single point scf calculations and answer your questions."""
)

# upload structure file into buffer
structure_file = st.file_uploader("Upload the structure file", type=("cif"))

# functional="PBE"
# mode="efficiency"

###############################################
### Generating QE input from structure file ###
###############################################

if not structure_file:
    st.info("Please add your structure file to continue")
if  structure_file:
    # create a local copy of structure file in the container
    save_directory = "./src/qe_input/temp/"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)

    
    file_name = structure_file.name
    file_path = os.path.join(save_directory, file_name)
    st.session_state['save_directory']=save_directory
    st.session_state['structure_file']=file_path

    with open(file_path, "wb") as f:
        f.write(structure_file.getbuffer())
    structure = Structure.from_file(file_path)
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
                                           pseudo_path, 
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
    
    # visualising the structure and printing info about the parameters

    # server=Flask(__name__)
    # app = Dash(__name__,server=server)
    app = Dash()
    structure_component = StructureMoleculeComponent(structure, id="structure")
    app.layout=html.Div([structure_component.layout()])
    def run_dash_app():
        app.run_server(debug=False, host="0.0.0.0", port=8055)

    thread = threading.Thread(target=run_dash_app, daemon=True)
    thread.start()
    time.sleep(3)
    st.components.v1.iframe(src="http://0.0.0.0:8055", height=600)
    
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
    
  
    st.write('compound: ', composition)
    st.write('Pseudo family used: ', pseudo_family)
    st.write('energy cutoff (Ry): ', cutoffs['max_ecutwfc'])
    st.write('density cutoff (Ry): ', cutoffs['max_ecutrho'])
    st.write('k spacing (1/A): ', 0.01)

    st.download_button(
            label="Download the files",
            data=open('./src/qe_input/qe_input.zip', "rb").read(),
            file_name='qe_input.zip',
            mime="application/octet-stream"
        )

    

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