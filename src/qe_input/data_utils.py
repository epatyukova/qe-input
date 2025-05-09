import os
import shutil
import re
import json
import pandas as pd
import numpy as np
from pymatgen.core.composition import Composition
from pymatgen.core.structure import Structure
from mp_api.client import MPRester
import streamlit as st
import requests
from bs4 import BeautifulSoup

@st.cache_data
def jarvis_structure_lookup(formula,id=False):
    df=pd.read_pickle('./src/qe_input/Jarvis.pkl')
    da=df.loc[df['formula']==formula]
    da.reset_index(inplace=True,drop=True)
    
    if not id:
        formulas=[]
        energy=[]
        groups=[]
        groups_j=[]
        natoms=[]
        abc=[]
        angles=[]
        jid=[]
        for i in range(len(da)):
            atoms=da['atoms'].values[i]
            structure=Structure(lattice=atoms['lattice_mat'],species=atoms['elements'],coords=atoms['coords'])
            groups.append(structure.get_space_group_info(symprec = 0.01, angle_tolerance = 5.0)[0])
            groups_j.append(da['spg_symbol'].values[i])
            structure=structure.get_reduced_structure()
            ABC=[round(x,2) for x in structure.lattice.abc]
            Angles=[round(x,1) for x in structure.lattice.angles]
            natoms.append(structure.num_sites)
            abc.append(ABC)
            angles.append(Angles)
            energy.append(da['formation_energy_peratom'].values[i])
            formulas.append(structure.formula)
            jid.append(da['jid'].values[i])

        result=pd.DataFrame()
        result['select']=np.zeros(len(formulas),dtype=bool)
        result['formula']=formulas
        result['form_energy_per_atom']=energy
        result['sg']=groups
        result['sg_jarvis']=groups_j
        result['natoms']=natoms
        result['abc']=abc
        result['angles']=angles
        result['id']=jid
        
        result=result.sort_values(by=['form_energy_per_atom'])
        result.reset_index(drop=True, inplace=True)
        return result
    else:
        dx=da.loc[da['jid']==id]
        atoms=dx['atoms'].values[0]
        structure=Structure(lattice=atoms['lattice_mat'],species=atoms['elements'],coords=atoms['coords'],coords_are_cartesian=True)
        return structure

@st.cache_data
def mp_structure_lookup(formula, mp_api_key, id=False):

    with MPRester(mp_api_key) as mpr:
        docs = mpr.materials.summary.search(
                formula=formula)
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