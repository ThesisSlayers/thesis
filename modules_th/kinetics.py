# AUTOGENERATED! DO NOT EDIT! File to edit: KINETICS.ipynb (unless otherwise specified).

__all__ = ['read_data', 'sometimes', 'wrapVideo', 'get_dsets', 'get_dls', 'setup_log', 'get_learner', 'save_learner']

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
from fastai.data.all import *
from fastai.distributed import *
import pandas as pd
from pathlib import Path
import time
from datetime import date
from vidaug import augmentors as va
import cv2

import torchvision.transforms as T

from .video_block import *
from .inflator import *
from .triplet_loss import *
from .supcon_module import *
from .cus_cbs import *

#Pretrained models
from .pretrained_r2p1d50 import *
from resnetmodels.mean import get_mean_std

# Cell
def read_data():
    items_path = '/mnt/data/adrianlopez/Datasets/kinetics700/kinetics_train.csv'
    return pd.read_csv(items_path, index_col=0)

# Cell
def sometimes(x):
    return va.Sometimes(0.5,x)

def wrapVideo(x):
    return Video(x)

# Cell
def get_dsets(df, l=2, size=512,skip=2,n_views=1):

    vid_pip = [ColReader('vid_files'),
               createVideoForm(l=l,skip=skip, form='img'),
               Resize(size, method=ResizeMethod.Pad),
#                sometimes(va.HorizontalFlip()),
#                va.GaussianBlur(1.),
               va.InvertColor(),
#                va.RandomRotate(10),
               wrapVideo]

    lbl_pip = [ColReader('label'), Categorize()]
    pip = [*([vid_pip]*n_views), lbl_pip]
    # Splits
    splits = ColSplitter('val')(df)

    # Datasets and dataloaders
    dsets = Datasets(df, pip, splits=splits)
    return dsets, splits

# Cell
def get_dls(dsets,splits,df, n_el= 2, n_lbl = 2, shuffle_fn=UniformizedShuffle, normalize='kinetics'):

    mean, std = get_mean_std(1,normalize)
    dls  = dsets.dataloaders(bs=n_el*n_lbl,
                             shuffle_train=True,
                             after_item=ToTensor(),
                             after_batch=[IntToFloatTensor(), Normalize.from_stats(*imagenet_stats)])

    dls.valid.shuffle = True
    if shuffle_fn is not None:
        dls.train.shuffle_fn = UniformizedShuffle(df.label.iloc[splits[0]], n_el = n_el, n_lbl= n_lbl)
        dls.valid.shuffle_fn = UniformizedShuffle(df.label.iloc[splits[1]], n_el = n_el, n_lbl= n_lbl)
    return dls
    True


# Cell
def setup_log(learn,name, append=True):
     # set up logs file
    # now = datetime.now()
    # time = now.strftimes("%d_%m")
    logs_file = '/mnt/data/eugeniomarinelli/UCF_experiments/training_results/logs_kinetics_'+name+'.csv'
    Logs_csv =   CSVLogger(fname= logs_file, append=append)
    learn.add_cb(Logs_csv)

# Cell
def get_learner(df,
                pretrained_model='r2p1d50_K',
                loss_name='CEL',
                l=40, size=224, n_lbl =2, n_el=2, skip=20, embs_size=256,n_views=2,
                normalize = 'kinetics'):

    dsets,splits = get_dsets(df, l, size, skip, n_views)

    dls = get_dls(dsets,splits,df, normalize=normalize)

    if pretrained_model in inserted_models:
        model = inserted_models[pretrained_model]
    else: raise 'model not present in pretrained models'


    body = create_body(model, cut=-2)



    if loss_name == 'SCL+CEL':
        Loss = SumLoss(SupConLoss,p='cos', alpha=1, n_views=n_views)
        head = inflate(create_head(256, len(dls.vocab), lin_ftrs=[]))
        model = MixedLossModel(body,head)
        metrics = [supcon_accuracy, silh_score]


    elif loss_name == 'SCL':
        Loss= SupConLoss()
        head = inflate(create_head(4096, embs_size, lin_ftrs=[]))
        model = nn.Sequential(body,head)
        metrics = [silh_score]


    elif loss_name == 'CEL':
        Loss = CEL()
        head = inflate(create_head(4096, len(dls.vocab), lin_ftrs=[256]))
        model = MixedLossModel(body,head)
        metrics = [supcon_accuracy,silh_score]

    elif loss_name == 'CEL_after_SCL':
        Loss = CrossEntropyLossFlat()
        saved_model = torch.load('/mnt/data/eugeniomarinelli/UCF_experiments/trained_models_cnn/models/r2p1d50_ucf101_SCL_tuned_15fr.pth')
        model = nn.Sequential(saved_model,nn.Sequential(nn.ReLU(inplace=True),LinBnDrop(256, 101, p=0.5)))
        metrics = [accuracy]
    else:
        raise 'Loss not implemented'



    learn = Learner(dls,
                model,
                splitter=splitter ,
                loss_func=Loss,
                metrics=metrics)

    if loss_name == 'SCL+CEL':
        learn.add_cbs([ContrastiveCallback(n_views)])#,LossesRecorderCallback()])
    elif loss_name == 'SCL':
        learn.add_cb(ContrastiveCallback(n_views))
    elif loss_name in ['CEL', 'CEL_after_SC']:
        learn.add_cb(MultiViewsCallback(n_views))
    time = date.today().strftime("_%d-%m")

    setup_log(learn, str(pretrained_model)+'_'+loss_name+'_tuning_10_'+time, append=True)

    return learn


# Cell
def save_learner(learn, name):
    prefix = '/mnt/data/eugeniomarinelli/'
    try:
        learn.export(prefix+'UCF_experiments/trained_models_cnn/learners/learner_kinetics_'+name)
    except: print("learner export didn't work")
    try:
        torch.save(learn.model,prefix+'UCF_experiments/trained_models_cnn/models/model_kinetics_'+name+'.pth')
    except: pass
    torch.save(learn.model.state_dict(),prefix+'UCF_experiments/trained_models_cnn/models/state_dict_kinetics_'+name)

