import streamlit as st
import numpy as np
import torch
from torch.utils.data import DataLoader
from pymatgen.io.cif import CifWriter

from cgcnn.model import CrystalGraphConvNet
from cgcnn.data import CIFData, collate_pool

data_type_np = np.float32
data_type_torch = torch.float32

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
    'robust_regression': True,
    'batch_size': 256,
    'base_lr': 0.01,
    'momentum': 0.9,
    'weight_decay': 0.1,
    'optim': 'SGD',
    'pin_memory': True,
    'patience': 50,
}

def predict_kspacing(structure, config=model_config):

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
                            classification=config['classification'],
                            robust_regression=config['robust_regression'])
    
    num_models=5

    all_predictions=np.zeros(num_models)
    all_std=np.zeros(num_models)

    for model_idx in range(num_models):
        checkpoint = torch.load('./src/qe_input/trained_models/'+'kspacing_checkpoint'+str(model_idx)+'.ckpt', map_location='cpu')
        model_weights = checkpoint["state_dict"]
        for key in list(model_weights):
            model_weights[key.replace("model.", "")] = model_weights.pop(key)
        model.load_state_dict(model_weights)
        model.eval()
        loader=DataLoader(dataset, batch_size=1, collate_fn=collate_pool)
        for batch in loader:
            graph, _, _ = batch
        output = model.forward(graph[0],graph[1],graph[2],graph[3])
        prediction, log_std = output.chunk(2, dim=-1)
        all_predictions[model_idx]=float(prediction)
        std=np.sqrt(np.exp(2.0 * float(log_std)))
        all_std[model_idx]=float(std)

    klength=all_predictions.mean()
    klength_stde=0
    klength_stda=0
    for model_idx in range(num_models):
        klength_stde+=(klength-all_predictions[model_idx])**2
        klength_stda+=all_std[model_idx]**2
    klength_std=(1/(1-num_models)*klength_stde+1/num_models*klength_stda)**0.5

    return klength, klength_std

