# AUTOGENERATED! DO NOT EDIT! File to edit: distributed_training.ipynb (unless otherwise specified).

__all__ = ['main']

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
from IPython.display import display, clear_output
from fastai.data.all import *
from fastai.distributed import *
from fastscript import *
import pandas as pd
from pathlib import Path
import time
import warnings
from datetime import date

# Cell
from modules_th.video_block import *
from modules_th.inflator import *
from modules_th.triplet_loss import *
from modules_th.supcon_module import *
from modules_th.cus_cbs import *



from modules_th.ucf101 import *

# Cell
@call_parse
def main(gpu          : Param("GPU to run on", int)            = None,
         n_epoch: Param("# of epochs to train", int)           = 0,
         freeze_epochs : Param("Frozen epochs", int)           = 15,
         n_lbl  :Param("# of different labels per batch", int) = 2 ,
         n_el   :Param("# of elements per label", int)         = 2,
         l      :Param("num of frames of the ResizeTime", int) = 30,
         skip   :Param("skip frames",int)                      = 2,
         size     :Param("size for Resize", int)               = 224,
         loss   :Param(" loss between CEL-SCL and SCL ", str)  = 'SCL',
         embs_size:Param("embeddings size", int)               = 256,
         n_views:Param("number of views", int)                 = 2,
         descr  :Param("description of the experiment", str)   = 'SCL  with 0 unfrozen and 15 frozen epoch',
         model: Param("model", str)                            = 'r2p1d50_K',
         normalize: Param('normalization',str)                 = 'kinetics'
        ):
    prefix = '/mnt/data/eugeniomarinelli/'

    if gpu is not None:
        gpu = setup_distrib(gpu)
        items = rank0_first(read_data)
    else:
        items = read_data()
    print('set up completed \n')

    learn = get_learner(items, model,  loss, l, size, n_lbl, n_el, skip, embs_size,n_views, normalize)
    print('Learner Loaded \n')
    
    
    
    torch.cuda.empty_cache()
    if gpu is not None:
        print("Distributed Data Parallel training started")
        with learn.distrib_ctx(gpu):
            print('starting distrib train \n')
            learn.fine_tune(n_epoch, freeze_epochs=freeze_epochs) 
    else:
        warnings.filterwarnings("ignore", message='.*nonzero.*', category=UserWarning)
        print("Data Parallel training started")
        with learn.parallel_ctx(device_ids=[0,1]):
            print('starting parallel train \n')
            learn.fine_tune(n_epoch, freeze_epochs=freeze_epochs)

    save_learner(learn, model+'15fr')

    time = date.today().strftime("%d-%m-%y")
    experiment = pd.DataFrame({'date':[time],
             'description':[descr],
             'l':[l],
             'skip':[skip],
             'size':[size],
             'loss':[loss],
             'n_el':[n_el],
             'n_lbl':[n_lbl],
             'n_epochs':[n_epoch],
             'freeze_epochs':[freeze_epochs]}).to_csv(prefix+'UCF_experiments/experiments_logs.csv',mode='a', header=False)
