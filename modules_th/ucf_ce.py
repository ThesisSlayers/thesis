# AUTOGENERATED! DO NOT EDIT! File to edit: UCF_Crimes_CEL.ipynb (unless otherwise specified).

__all__ = ['read_data', 'get_learner', 'play_video']

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
from fastai.data.all import *
from fastai.distributed import *
import pandas as pd
from pathlib import Path
import time
from vidaug import augmentors as va

import torchvision.transforms as T


# Cell
from .video_block import *
from .inflator import *
from .triplet_loss import *
from .supcon_module import *
from .cus_cbs import *

# Cell
def read_data():
    prefix = '/mnt/data/eugeniomarinelli/'
    items_path = prefix + 'UCF_experiments/training_cnn_ucf.csv'
    return pd.read_csv(items_path, index_col=0)

# Cell
def get_learner(df, loss='CE', l=40, size=224, n_lbl =4, n_el=2, skip=20, embs_size=128,n_views=1):
    vid_paths = df.vid_files.values

    sometimes = lambda x:va.Sometimes(0.5,x)

    vid_pip = [createVideoForm(l=l,skip=skip, form='img'),
               Resize(size, pad_mode='pad'),
               sometimes(va.HorizontalFlip()),
               va.GaussianBlur(1.),
               sometimes(va.InvertColor()),
               va.RandomRotate(10),
               lambda x: Video(x)]

    lbl_pip = [parent_label, Categorize()]
    pip = [vid_pip, lbl_pip]
    #splits
    splits = ColSplitter('val')(df)

    # Datasets and dataloaders
    dsets = Datasets(vid_paths, pip, splits=splits)

    dls  = dsets.dataloaders(bs=n_el*n_lbl,
                             shuffle_train=True,
                             after_item=ToTensor(),
                             after_batch=[IntToFloatTensor(), Normalize.from_stats(*imagenet_stats)])

#     dls.valid.shuffle = True
#     dls.train.shuffle_fn = UniformizedShuffle(df.lbls.iloc[splits[0]], n_el = n_el, n_lbl= n_lbl)
#     dls.valid.shuffle_fn = UniformizedShuffle(df.lbls.iloc[splits[1]], n_el = n_el, n_lbl= n_lbl)

    head, body = inflate(create_head(4096, len(dls.vocab), lin_ftrs=[embs_size])), inflate(create_body(resnet50, cut=-2))


    model = nn.Sequential(body, head)


    learn = Learner(dls,
                model,

                splitter=lambda model : [params(model[0]), params(model[1])],
                loss_func=CrossEntropyLossFlat(),
               metrics=accuracy)



    return learn


# Cell
#################
# SHOW VIDEO    #
#################
import time
import pylab as pl
from torchvision.io import read_video
from IPython.display import clear_output, display
def play_video(path='/mnt/data/eugeniomarinelli/UCF_Crimes/Videos/Burglary/Burglary003_x264.mp4', skip=20):
    vid, aud, dic = read_video(path,pts_unit='sec')
    for i in range(vid.size(0)):

        if i%skip==0:
            clear_output(wait=True)
            TensorImage(vid[i]).show()
            display(pl.gcf())
            time.sleep(0.01)
        print(i)
#clear_output()