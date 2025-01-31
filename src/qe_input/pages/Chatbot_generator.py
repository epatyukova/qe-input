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
import langgraph

st.title("Generate QE input with an LLM Agent")

if 'all_info' not in st.session_state.keys():
    st.session_state['all_info']=False

with st.sidebar:

    openai_api_key = st.text_input("OpenAI API Key ([Get an OpenAI API key](https://platform.openai.com/account/api-keys))", 
                                   key="feedback_api_key", 
                                   type="password",
                                   )

    llm_name_value = st.selectbox('assistant LLM', 
                        ("gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo'), 
                        index=None, 
                        placeholder='gpt-4o')

if llm_name_value:
    st.session_state['llm_name'] = llm_name_value
else:
    st.session_state['llm_name'] = 'gpt-4o'

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")

if not (st.session_state['all_info']):
    st.info("Please provide all necessary material information on the Intro page")

if openai_api_key and st.session_state['all_info']:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)
    st.markdown('**You can ask agent to correct any input parameters, ask about their meaning, or generate aiida code to run calculations!**')
    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if(message["role"]=="user" or message["role"]=="assistant"):
            st.markdown(message["content"])

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