import streamlit as st
from openai import OpenAI
from groq import Groq
import google.generativeai as genai
from utils import atomic_positions_list, generate_kpoints_grid, generate_response, convert_openai_to_gemini, gemini_stream_to_streamlit

input_file_schema="Below is the QE input file for SCF calculations for NaCl. Can you generate the \
                    similar one for my compound for which I will give parameters? \
                    Check line by line that only material parameters are different.\
                    &CONTROL\
                    pseudo_dir       = './'\
                    calculation      = 'scf'\
                    restart_mode     = 'from_scratch'\
                    tprnfor          = .true.\
                    /\
                    &SYSTEM\
                    ecutwfc          = 40  ! put correct energy cutoff here\
                    ecutrho          = 320 ! put correct density cutoff here\
                    occupations      = 'smearing'\
                    degauss          = 0.01 ! you can change the number\
                    smearing         = 'cold' ! choose correct smearing method\
                    ntyp             = 2 ! put correct number of atoms types\
                    nat              = 2 ! put correct number of atoms\
                    ibrav            = 0\
                    /\
                    &ELECTRONS\
                    electron_maxstep = 80\
                    conv_thr         = 1e-10\
                    mixing_mode      = 'plain'\
                    mixing_beta      = 0.4\
                    / \
                    ATOMIC_SPECIES \
                    Na 22.98976928 na_pbe_v1.5.uspp.F.UPF \
                    Cl 35.45 cl_pbe_v1.4.uspp.F.UPF \
                    K_POINTS automatic\
                    9 9 9  0 0 0\
                    CELL_PARAMETERS angstrom\
                    3.43609630987442 0.00000000000000 1.98383169159751\
                    1.14536543840311 3.23958308210503 1.98383169547732\
                    0.00000000000000 0.00000000000000 3.96766243000000\
                    ATOMIC_POSITIONS angstrom \
                    Na 0.0000000000 0.0000000000 0.0000000000\
                    Cl 2.2907350089 1.6197900184 3.9676599923\
                     "

st.title("Generate QE input with an LLM Agent")

groq_api_key=None
openai_api_key=None
gemini_api_key=None

if 'all_info' not in st.session_state.keys():
    st.session_state['all_info']=False

with st.sidebar:
    llm_name_value = st.selectbox('assistant LLM', 
                        ('llama-3.3-70b-versatile','gemini-2.0-flash', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'), 
                        index=None, 
                        placeholder='llama-3.3-70b-versatile')

    if llm_name_value in ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']:
        openai_api_key = st.text_input("OpenAI API Key ([Get an OpenAI API key](https://platform.openai.com/account/api-keys))", 
                                    key="openai_api_key", 
                                    type="password",
                                    )
    elif llm_name_value in ['llama-3.3-70b-versatile']:
        groq_api_key = st.text_input("Groq API Key ([Get an Groq API key](https://console.groq.com/keys))", 
                                   key="groq_api_key", 
                                   type="password",
                                   )
    elif llm_name_value in ['gemini-2.0-flash']:
        gemini_api_key = st.text_input ("Gemini API Key ([Get Gemini API Key](https://aistudio.google.com/apikey))",
                                        key="groq_api_key", 
                                        type="password",
                                        )
    if llm_name_value in ['llama-3.3-70b-versatile']:
        st.session_state['llm_name'] = llm_name_value
    elif llm_name_value in ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']:
        st.session_state['llm_name'] = llm_name_value
    elif llm_name_value in ['gemini-2.0-flash']:
        st.session_state['llm_name'] = llm_name_value
    else:
        st.session_state['llm_name'] = 'gpt-4o'

    if not openai_api_key:
        if llm_name_value in ["gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo']:
            st.info("Please add your OpenAI API key to continue.", icon="🗝️")

    if not groq_api_key:
        if llm_name_value in ['llama-3.3-70b-versatile']:
            st.info("Please add your Groq API key to continue.", icon="🗝️")
    
    if not gemini_api_key:
        if llm_name_value in ['gemini-2.0-flash']:
            st.info("Please add your Gemini API key to continue.", icon="🗝️")

if not (st.session_state['all_info']):
    st.info("Please provide all necessary material information on the Intro page")


if (openai_api_key or groq_api_key or gemini_api_key) and st.session_state['all_info']:
    # Create an OpenAI client.
    if llm_name_value in ["gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo']:
        client = OpenAI(api_key=openai_api_key)
    elif llm_name_value in ['llama-3.3-70b-versatile']:
        client = Groq(api_key=groq_api_key)
    elif llm_name_value in ['gemini-2.0-flash']:
        genai.configure(api_key=gemini_api_key)
        client = genai.GenerativeModel("gemini-2.0-flash")

    st.markdown('** Ask the agent to generate an input QE SCF file for the compound you uploaded**')
    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.

    cell_params=st.session_state['structure'].lattice.matrix

    atomic_positions=atomic_positions_list(st.session_state['structure'])
    kpoints=generate_kpoints_grid(st.session_state['structure'], st.session_state['kspacing'])

    task=f"You are the assitant for generation input file for single point \
              energy calculations with Quantum Espresso. If the user asks to generate an input file, \
              the following information is availible to you: \
              the formula of the compound {st.session_state['composition']},\
              the list of pseudo potential files {st.session_state['list_of_element_files']},\
              the path to pseudo potential files './',\
              the cell parameters in angstroms {cell_params},\
              the atomic positions in angstroms {atomic_positions},\
              the energy cutoff is {st.session_state['cutoffs'][ 'max_ecutwfc']} in Ry,\
              the density cutoff is {st.session_state['cutoffs'][ 'max_ecutrho']} in Ry,\
              kpoints automatic are {kpoints}, \
              number of atoms is {len(st.session_state['structure'].sites)} \
              Please calculate forces, and do gaussian smearing for dielectrics and semiconductors \
              and cold smearing for metals.  Try to assess whether the provided compound is \
              metal, dielectric or semiconductor before generation."
    

    if "messages" not in st.session_state:
        st.session_state.messages=[{"role": "system", "content": task}]
        st.session_state.messages.append({"role": "system", "content": input_file_schema})
    else:
        for message in st.session_state.messages:
            if message['role']=='system':
                message['content']=task+' '+input_file_schema
            

    for message in st.session_state.messages:
        if(message["role"]=="user"):
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif(message["role"]=="assistant"):
            with st.chat_message("assistant"):
                st.markdown(message["content"])


    if prompt := st.chat_input("Do you have any questions?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate a response using the OpenAI API.
        if st.session_state['llm_name'] in ["gpt-4o", "gpt-4o-mini", 'gpt-3.5-turbo']:
            stream = client.chat.completions.create(
                model=st.session_state['llm_name'],
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                temperature=0,
                stream=True,
            )
        elif st.session_state['llm_name'] in ['llama-3.3-70b-versatile']:
            stream = generate_response(messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                                       client=client,
                                       llm_model=st.session_state['llm_name'])
        elif st.session_state['llm_name'] in ['gemini-2.0-flash']:
            gemini_prompt=convert_openai_to_gemini(st.session_state.messages)
            stream=gemini_stream_to_streamlit(client.generate_content(gemini_prompt, 
                                           generation_config={"temperature": 0},
                                           stream=True))
            
        # Stream the response to the chat using `st.write_stream`, then store it in 
        # session state.
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        
        st.session_state.messages.append({"role": "assistant", "content": response})