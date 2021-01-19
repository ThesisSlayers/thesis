# AUTOGENERATED! DO NOT EDIT! File to edit: 06_distributed_inflated_NN.ipynb (unless otherwise specified).

__all__ = []

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
from video_block import *
from inflator import *
from triplet_loss import *
from supcon_module import *
from cus_cbs import *
import warnings
from datetime import datetime

from ucf_cnn import *

# Internal Cell
@call_parse
def main(gpu    :Param("GPU to run on", int)=None,
         file   :Param("csv path", bool)='UCF_experiments/train_UCF.csv',
         n_lbl  :Param("# of different labels per batch", int)=4,
         n_el   :Param("# of elements per label", int)=2,
         l      :Param("Target number of frames of the ResizeTime transform", int)=60,
         skip   :Param("skip frames",int)=20,
         sz     :Param("size for Resize", int)=224,
         n_epoch:Param("# of epochs to train", int)=10,
         loss   :Param("Choose a loss between CEL-SCL and SCL ", str)='CEL-SCL',
         embs_sz:Param("embeddings size", int)=128,
         n_views:Param("number of views", int)=2,
         log_nm :Param("logs file name. if 'date' the name will be composed by the date", str)='date'
         descr  :Param("description of the experiment", str)='First training with mixed SupConLoss to have a preformance baseline; first trial with a large skip'
        ):
    prefix = '/mnt/data/eugeniomarinelli/'
    items_path = prefix + file
    if gpu is not None:
        gpu = setup_distrib(gpu)
        items = rank0_first(lambda: pd.read_csv(items_path, index_col=0))
    else:
        items = pd.read_csv(items_path, index_col=0)

    learn = get_learner(items, loss=loss, l, sz, n_lbl , n_el, skip, embs_sz,n_views)
    print('Learner Loaded \n')
    
    
    # set up logs file
    now = datetime.now()
    time = now.strftime("%d_%m_h%H")
    Logs_csv =   CSVLogger(fname='logs_'+time+'.csv', append=False) if log_nm == 'date' else CSVLogger(fname='logs_'+log_nm+'.csv', append=False) 

    torch.cuda.empty_cache()
    if gpu is not None:
        print("Distributed Data Parallel training started")
        with learn.distrib_ctx(gpu):
            learn.fine_tune(n_epoch,cbs=[Logs_csv])
    else:
        warnings.filterwarnings("ignore", message='.*nonzero.*', category=UserWarning)
        print("Data Parallel training started")
        with learn.parallel_ctx(device_ids=[0,1]):
            learn.fine_tune(n_epoch,cbs=[Logs_csv])

    learn.save(prefix+'UCF_experiments/trained_models_cnn/ucf_cnn_'+time)
    kwrgs = set_kwrgs(loss, 1, 'cos', '0.5')
    save_losses(prefix+'UCF_experiments/training_results/ucf_cnn_'+time, loss, kwrgs)
    experiment = pd.DataFrame({'date':time,
             'description':descr,
             'l':l,
             'skip':skip,
             'size':sz,
             'loss':loss,
             'n_el':n_el,
             'n_lbl':n_lbl,
             'n_epochs':n_epochs}).to_csv(prefix+'UCF_experiments/experiments_logs.csv', mode='a')
    