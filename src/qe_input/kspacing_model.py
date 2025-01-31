import streamlit as st
import numpy as np
import torch
from torch.utils.data import DataLoader
from pymatgen.io.cif import CifWriter

from cgcnn.model import CrystalGraphConvNet
from cgcnn.data import CIFData, collate_pool

data_type_np = np.float32
data_type_torch = torch.float32

jarvis_stat={'mean': 43.78969486328977, 'std': 20.44467702225091}

model_config={
    'root_dir': './src/qe_input/cgcnn/cgcnn_data',
    'train_ratio': 0.8,
    'val_ratio':0.1,
    'test_ratio':0.1,
    'atom_fea_len': 64,
    'n_conv': 3,
    'h_fea_len': 128,
    'n_h': 1,
    'classification': False,
    'batch_size': 256,
    'base_lr': 0.01,
    'momentum': 0.9,
    'weight_decay': 0.1,
    'optim': 'SGD',
    'pin_memory': True,
    'patience': 50,
}

class Normalizer(object):
    """Normalize a Tensor and restore it later. """

    def __init__(self, state_dict):
        """tensor is taken as a sample to calculate the mean and std"""
        self.mean = state_dict['mean']
        self.std = state_dict['std']

    def norm(self, tensor):
        return (tensor - self.mean) / self.std

    def denorm(self, normed_tensor):
        return normed_tensor * self.std + self.mean


def predict_kspacing(structure, training_stat=jarvis_stat,config=model_config):
    normalizer=Normalizer(state_dict=training_stat)

    file_name='./src/qe_input/cgcnn/cgcnn_data/0.cif'
    write_cif=CifWriter(structure)
    write_cif.write_file(file_name)

    dataset = CIFData(root_dir=config['root_dir'], max_num_nbr=12, radius=10, dmin=0, step=0.2, random_seed=123)
    structures, _, _ = dataset[0]
    orig_atom_fea_len = structures[0].shape[-1]
    nbr_fea_len = structures[1].shape[-1]

    model=CrystalGraphConvNet(orig_atom_fea_len=orig_atom_fea_len,
                            nbr_fea_len=nbr_fea_len,
                            atom_fea_len=config['atom_fea_len'], 
                            n_conv=config['n_conv'], 
                            h_fea_len=config['h_fea_len'], 
                            n_h=config['n_h'],
                            classification=config['classification'])
    
    checkpoint = torch.load('./src/qe_input/trained_models/kspacing_checkpoint.ckpt')

    model_weights = checkpoint["state_dict"]
    for key in list(model_weights):
        model_weights[key.replace("model.", "")] = model_weights.pop(key)
    model.load_state_dict(model_weights)
    model.eval()

    loader=DataLoader(dataset, batch_size=1, collate_fn=collate_pool)
    for batch in loader:
        graph, _, _ = batch
    
    output = model.forward(graph[0],graph[1],graph[2],graph[3])
    klength = normalizer.denorm(float(output))
    kspacing = round(1 / klength , 4)

    return kspacing

