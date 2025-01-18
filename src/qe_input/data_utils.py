import os
import shutil
import re
import json
import pandas as pd
import numpy as np
from pymatgen.core.composition import Composition
from pymatgen.core.structure import Structure
from jarvis.db.figshare import data
from mp_api.client import MPRester
import streamlit as st
import requests
from bs4 import BeautifulSoup

@st.cache_data
def jarvis_structure_lookup(formula):
    dft_3d = data('dft_3d')
    df=pd.DataFrame(dft_3d)
    da=df.loc[df['formula']==formula]
    da.reset_index(inplace=True,drop=True)
    lowest_energy_index=0
    lowest_energy=da.iloc[0]['formation_energy_peratom']
    if(len(da)>1):
        for i in range(1,len(da)):
            energy=da.iloc[i]['formation_energy_peratom']
            if(energy<lowest_energy):
                lowest_energy=energy
                lowest_energy_index=i
    atoms=da.iloc[lowest_energy_index]['atoms']
    structure=Structure(lattice=atoms['lattice_mat'],species=atoms['elements'],coords=atoms['coords'])
    return structure

@st.cache_data
def mp_structure_lookup(formula, mp_api_key):
    with MPRester(mp_api_key) as mpr:
        docs = mpr.materials.summary.search(
                formula=formula, is_stable="True"
                )
    lowest_energy_index=0
    lowest_energy=docs[0].energy_per_atom
    if(len(docs)>1):
        for i in range(1,len(docs)):
            energy=docs[i].energy_per_atom
            if(energy<lowest_energy):
                lowest_energy=energy
                lowest_energy_index=i
    structure=docs[lowest_energy_index].structure
    return structure

def mc3d_structure_lookup(formula):
    df=pd.read_json('./src/qe_input/mc3d_structures/mc3d_filtered_entries_pbe-v1_2025-01-16-01-09-20.json')
    formula=Composition(formula).hill_formula

    da=df.loc[df['formula_hill']==formula]
    da.reset_index(inplace=True,drop=True)
    lowest_energy_index=0
    lowest_energy=da['total_energy'].values[0]

    if(len(da)>1):
        for i in range(1,len(da)):
            energy=da['total_energy'].values[i]
            if(energy < lowest_energy):
                lowest_energy=energy
                lowest_energy_index=i
    ID=da['id'].values[lowest_energy_index]   
    structure_file='./src/qe_input/mc3d_structures/mc3d-pbe-cifs/'+ID[:-7]+'-pbe.cif' 
    structure=Structure.from_file(structure_file)
    return structure

def oqmd_strucutre_lookup(formula):
    response = requests.get('http://oqmd.org/oqmdapi/formationenergy?composition='+formula+'&limit=50&')
    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')
    content=json.loads(soup.text)
    lowest_energy_index=0
    lowest_energy=content['data'][0]['delta_e']
    if(len(content['data'])>1):
        for i in range(1,len(content['data'])):
            energy=content['data'][i]['delta_e']
            if(energy<lowest_energy):
                lowest_energy=energy
                lowest_energy_index=i
    species=[]
    coords=[]
    for line in content['data'][0]['sites']:
        el, merged_coord = line.split(' @ ')
        species.append(el)
        x,y,z=merged_coord.split(' ')
        coords.append([float(x),float(y),float(z)])
    structure=Structure(lattice=content['data'][lowest_energy_index]['unit_cell'],species=species,coords=coords)
    return structure