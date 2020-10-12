# AUTOGENERATED! DO NOT EDIT! File to edit: 03_video_block.ipynb (unless otherwise specified).

__all__ = ['show_frames', 'Video', 'ResizeTime', 'encodes', 'encodes', 'uniformize_dataset', 'get_vid_files',
           'UniformLabelsCallback', 'snippets_from_video']

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
import time
from IPython.display import display, clear_output
from fastai.data.all import *
import pandas as pd
from pathlib import Path
import regex as re
import numpy as np

# Cell
def show_frames(video,start=0, end=5):
    '''show frames in a video from start to end'''
    for frame in video[start:end]:
        clear_output(wait=True)
        frame.show()
        time.sleep(0.5)


# Cell
class Video(L):
    ''' the init function takes a list of PILImage s'''
    @classmethod
    def create(cls, paths:Union[list,str], sep='\n'):
        '''create images from frames path in a video'''
        paths = paths.split(sep) if isinstance(paths, str) else paths
        return cls(map(PILImage.create, paths))


# Cell
class ResizeTime(Transform):
    split_idx = None # 0- train 1- validation
    def __init__(self, skip=2, l=50, drop_last=True,**kwargs):
        self.skip = skip
        self.l = l
        self.drop_last = drop_last
        #self.split_idx=split_idx
        super().__init__(**kwargs)

    def encodes(self, vid:Video):
        '''create a list of frame-images (snippet) out a single video path'''
        l, skip = self.l, self.skip
        snippet_list = snippets_from_video(vid,s=skip,l=l)
        idx = len(snippet_list)//2 if self.split_idx else random.randint(0,len(snippet_list)-1) # ** if validation always takes middle snip
        return snippet_list[idx]

# Cell
@ToTensor
def encodes(self, vid:Video):
    img2tens=ToTensor()
    return torch.cat([img2tens(frame)[None] for frame in vid])


# Cell
def _get_sz(x):
    if isinstance(x, tuple): x = x[0]
    if not isinstance(x, Tensor): return fastuple(x.size)
    return fastuple(x.get_meta('img_size', x.get_meta('sz', (x.shape[-1], x.shape[-2]))))

@Resize
def encodes(self, video:Video):
        nw_vid=[]
        for frame in video:
            orig_sz = _get_sz(frame)
            w,h = orig_sz
            op = (operator.lt,operator.gt)[self.method==ResizeMethod.Pad]
            m = w/self.size[0] if op(w/self.size[0],h/self.size[1]) else h/self.size[1]
            cp_sz = (int(m*self.size[0]),int(m*self.size[1]))
            tl = fastuple(int(self.pcts[0]*(w-cp_sz[0])), int(self.pcts[1]*(h-cp_sz[1])))
            fastaiImg = PILImage.create(np.array(frame.crop_pad(cp_sz, tl, orig_sz=orig_sz, pad_mode=self.pad_mode,
                       resize_mode=self.mode_mask if isinstance(frame,PILMask) else self.mode, resize_to=self.size)))
            nw_vid.append(fastaiImg)
        return Video(nw_vid)


# Cell
def uniformize_dataset(vds, lbls, n=3, shuffle=True):
    if shuffle: random.shuffle(lbls)
    vocab = list(set(lbls))
    lbl2vds = {lbl:[] for lbl in vocab}
    for i, lbl in enumerate(lbls): lbl2vds[lbl].append(i)
    idxs = []
    while len(vocab)!=0:
        lbl = random.choice(vocab)
        for i in range(n):
            try:
                idx = lbl2vds[lbl].pop()
                idxs.append(idx)
            except IndexError:
                vocab.remove(lbl)
                break
    return vds[idxs], lbls[idxs]

def get_vid_files(path:(Path, str), index_col=0, sep='\n'):
    df = pd.read_csv(path, index_col=0)
    vds = L([paths.split(sep) for paths in df['paths']])
    lbls = df['lbl']
    return uniformize_dataset(vds, lbls)

# Cell
class UniformLabelsCallback(Callback):
#     def __init__(self, path):
#         super().__init__()
#         self.path = path

    def after_epoc(self):
        vds, lbls = uniformize_dataset(*self.dls.items)
        dls = dls.new(bs=40)
        #######
        # Create new datasets and dataloaders from newly oredered items
        #######
        self.learn.dls = dls.new(items=(vds,lbls))

# Cell
def snippets_from_video(vid, l=10, s=2):
    '''create list of snippet out a video'''
    vid=vid[::s] # skip frames
    return [[vid[i] for i in range(k*l, k*l + l)] for k in range(0,len(vid)//l)]