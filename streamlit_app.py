import streamlit as st
from openai import OpenAI
from pymatgen.core.structure import Structure
from pymatgen.core.composition import Composition
from utils import list_of_pseudos, cutoff_limits, generate_input_file


import os
import shutil
import json

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="feedback_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    functional = st.selectbox('XC-functional', 
                              ('PBE','PBEsol'), 
                              index=None, 
                              placeholder='PBE')
    mode = st.selectbox('pseudopotential flavour', 
                        ('efficiency','precision'), 
                        index=None, 
                        placeholder='efficiency')
    llm_name = st.selectbox('assistant LLM', 
                        ("gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo'), 
                        index=None, 
                        placeholder='gpt-4o')

# Show title and description.
st.title("💬 Chatbot for QE input")

st.write(
    "To generate input file, provide structure CIF file."
    "The Chatbot will generate an input file for QE single point scf calculations and answer your questions."
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
    save_directory = "./temp"
    if os.path.exists(save_directory):
        shutil.rmtree(save_directory, ignore_errors=True)
    os.makedirs(save_directory)
    
    file_name = structure_file.name
    file_path = os.path.join(save_directory, file_name)

    with open(file_path, "wb") as f:
        f.write(structure_file.getbuffer())
    structure = Structure.from_file(file_path)
    composition = Composition(structure.alphabetical_formula)
    
    pseudo_path="./temp/pseudos/"
    if not os.path.exists(pseudo_path):
        os.makedirs(pseudo_path)
    
    if not functional:
        functional='PBE'
    if not mode:
        mode='efficiency'

    pseudo_family, list_of_element_files=list_of_pseudos('./pseudos/', functional, mode, composition,pseudo_path)
    cutoffs=cutoff_limits('./pseudo_cutoffs/', functional, mode, composition)
    
    st.write('compound: ', composition)
    st.write('Pseudo family used: ', pseudo_family)
    st.write('energy cutoff (Ry): ', cutoffs['max_ecutwfc'])
    st.write('density cutoff (Ry): ', cutoffs['max_ecutrho'])
    st.write('k spacing (1/A): ', 0.01)

    shutil.make_archive('qe_input', 'zip', './temp')
    input_file_content=generate_input_file(save_directory, 
                                           structure_file, 
                                           pseudo_path, 
                                           list_of_element_files, 
                                           cutoffs['max_ecutwfc'], 
                                           cutoffs['max_ecutrho'], 
                                           kspacing=0.01)
    shutil.make_archive('qe_input', 'zip', './temp')
    
    st.download_button(
        label="Download the files",
        data=open('./qe_input.zip', "rb").read(),
        file_name='qe_input.zip',
        mime="application/octet-stream"
    )
###############################################
### LLM part to answer questions            ###
###############################################
# from agent import define_model
from langchain_openai import ChatOpenAI

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
if openai_api_key:
    # Create an OpenAI client.
    # client = OpenAI(api_key=openai_api_key)
    if not llm_name:
        llm_name='gpt-4o'
    client=ChatOpenAI(llm_name,openai_api_key,temperature=0)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
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
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})