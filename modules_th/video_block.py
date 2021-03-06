# AUTOGENERATED! DO NOT EDIT! File to edit: 07_read_video_function.ipynb (unless otherwise specified).

__all__ = ['show_frames', 'Video', 'snippets_from_video', 'stretch', 'ResizeTime', 'TensorVideo', 'encodes', 'encodes',
           'TensorVideo', 'encodes', 'encodes', 'encodes', 'repeat_video', 'create_video', 'createVideoForm',
           'uniformize_dataset', 'UniformizedShuffle', 'repeat_video', 'initialize_start_end', 'create_video',
           'createVideoForm', 'RandomCrop', 'RandomHFlip', 'RandomColorJitter']

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
from fastai.data.all import *
from IPython.display import display, clear_output
import pandas as pd
import numpy as np
from pathlib import Path
import time
import torchvision.transforms as T
import cv2

# Cell
def show_frames(video,start=0, end=5):
    '''show frames in a video from start to end'''
    for frame in video[start:end]:
        clear_output(wait=True)
        frame.show()
        time.sleep(0.5)

# Cell
@patch
def insert(l:L, i, o):
    l.items.insert(i, o)

class Video(L):
    @classmethod
    def create(cls, paths, sep='\n'):
        '''create images from frames path in a video'''
        paths = paths.split(sep) if isinstance(paths, str) else paths
        return cls(map(PILImage.create, paths))

    def show(self, i=None):
        if i == None: i = random.randint(0, len(self)-1)
        show_image(self[i])

    def __mul__(self, n):
        neg = n < 0
        if n==0 or abs(n) >=1: return self[[(i+neg)//n for i in range(abs(int(n))*len(self))]]
        else: return self/(1/n)

    def __truediv__(self, n):
        n = int(n)
        return self[::n]

    def __rmul__(self, n):
        return self*n

    def __getitem__(self, idx): return self._get(idx) if is_indexer(idx) else Video(self._get(idx), use_list=None)


# Cell
def snippets_from_video(vid, l=10, s=2):
    '''create list of snippet out a video'''
    vid=vid[::s] # skip frames
    return [Video([vid[i] for i in range(k*l, k*l + l)]) for k in range(0,len(vid)//l)]

def stretch(vid, l):
    vid = vid*(l//len(vid))
    if len(vid) == l: return vid
    lv = len(vid)
    n = l - lv                     # Number of frames to be inserted
    d = lv//n                      # Number of frames between inserted frames
    idxs = L(range(lv))
    for i in range(n):
        idxs.insert((d+1)*i, d*i)
    return vid[idxs]

class ResizeTime(Transform):
    split_idx = None # 0- train 1- validation
    def __init__(self, skip=2, l=50, drop_last=True,**kwargs):
        self.skip = skip
        self.l = l
        self.drop_last = drop_last
        super().__init__(**kwargs)

    def encodes(self, vid:Video, split_idx=split_idx):
        '''create a list of frame-images (snippet) out a single video path'''
        l, skip, l_vid = self.l, self.skip, len(vid)
        if l_vid > l*skip:
            snippet_list = snippets_from_video(vid,s=skip,l=l)
            idx = len(snippet_list)//2 if split_idx else random.randint(0,len(snippet_list)-1) # ** if validation always takes middle snip
            return snippet_list[idx]
        else:
            vid = vid[::skip]
            vid = stretch(vid, l)
        return vid

# Cell
class TensorVideo(TensorBase): pass

@ToTensor
def encodes(self, vid:Video):
    return TensorVideo(vid.stack().permute(3,0,1,2))

# Cell
@Resize
def encodes(self, video:Video):
    return video.map(partial(Resize.encodes[PILImage], self))

# Cell
class TensorVideo(TensorBase):
    def show(self, i=None):
        if i == None: i = random.randint(0, self.size(1)-1)
        show_image(self[:,i])

@ToTensor
def encodes(self, vid:Video):
    return TensorVideo(vid.stack().permute(3,0,1,2))

@Resize
def encodes(self, video:TensorVideo):
    return T.Resize(self.size)(video)

# Cell
@IntToFloatTensor
def encodes(self, vid:TensorVideo):
    return vid.float()/self.div if vid.dtype==torch.uint8 else vid

# Cell
def repeat_video(vid, l):
    """Repeats video "vid" until it reaches target length "l" """
    reap = l // len(vid)
    delta = l % len(vid)
    vid = vid * reap + vid[0:delta]
    return vid

def create_video(vid_path, start=None, l=50, skip=3, form='tens'):
    assert form in ['tens', 'img'], "form should be either 'tens' or 'img'"
    vidcap = cv2.VideoCapture(str(vid_path))
    duration = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)

    if l=='all': start, l = 0, duration//skip
    elif start is None: start = random.randint(0, max(0, duration-l*skip))
    vid = L()
    for i, frame_pos in enumerate(range(start, start+l*skip, skip)):
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        res, frame = vidcap.read()
        if res: vid.append(frame)
        else: vid = repeat_video(vid, l); break

    vidcap.release()
    if form == 'tens': return TensorVideo(vid.stack().permute(3,0,1,2))
    else: return vid.map(PILImage.create)


class createVideoForm(Transform):
    '''Create a TensorVideo using form=tens or a list of PIL images using form=img '''
    def __init__(self, l='all', skip=3, form='tens'):
        self.l = l
        self.skip = skip
        self.form = form
    def encodes(self, vid_path): return create_video(vid_path, l=self.l, skip=self.skip, form=self.form)

# Cell
def uniformize_dataset(items, lbls, vocab=None, n_el=3, n_lbl=3, shuffle=True):
    if vocab is None: vocab = list(set(lbls))
    lbl2idxs = {lbl:[] for lbl in vocab}
    for i, lbl in enumerate(lbls): lbl2idxs[lbl].append(i)
    for lbl, idxs in lbl2idxs.items():
        if len(idxs) < n_el: vocab.remove(lbl)
    if shuffle: [random.shuffle(v) for v in lbl2idxs.values()]
    idxs = []
    while len(vocab) >= n_lbl:
        lbl_samples = random.sample(vocab, n_lbl)
        for lbl in lbl_samples:
            i = 0
            while i < n_el:
                i += 1
                idx = lbl2idxs[lbl].pop()
                idxs.append(idx)
            if len(lbl2idxs[lbl]) <= n_el:
                vocab.remove(lbl)
    return [items[idx] for idx in idxs] if isinstance(items, list) else getattr(items, 'iloc', items)[idxs]

# Cell
class UniformizedShuffle():
    def __init__(self, lbls, vocab=None, n_el=4, n_lbl=4):
        self.lbls = lbls
        if vocab is None: vocab = list(set(lbls))
        self.vocab = vocab
        self.n_el = n_el
        self.n_lbl = n_lbl
    def __call__ (self, items):
        return uniformize_dataset(items, lbls=self.lbls.copy(), vocab=self.vocab.copy(), n_el=self.n_el, n_lbl=self.n_lbl)

# Cell
import os
import cv2
import random
import torchvision.transforms as T

# Cell
def repeat_video(vid, l):
    """Repeats video "vid" until it reaches target length "l" """
    reap = l // len(vid)
    delta = l % len(vid)
    vid = vid * reap + vid[0:delta]
    return vid

def initialize_start_end(start, end, l, duration, skip):
    if l=='all': start, end, l = 0, duration, duration//skip
    else:
        if start is None and end is None:
            start = random.randint(0, max(0, duration-l*skip))
            end = start + l*skip
        elif start is None: start = random.randint(0, max(0, end-l*skip))
        elif end is None: end = start + l*skip
    return start, end

def create_video(vid_path, start=None, end=None, l=50, skip=4, form='tens'):
    assert os.path.exists(str(vid_path)), f"Path {vid_path} doesn't exist"
    assert form in ['tens', 'img'], "form should be either 'tens' or 'img'"
    vidcap = cv2.VideoCapture(str(vid_path))
    duration = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    start, end = initialize_start_end(start, end, l, duration, skip)

    vid = L()
    for frame_pos in range(start, min(start+l*skip, end), skip):
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
        res, frame = vidcap.read()
        if res: vid.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        else:
            if len(vid)==0:
                raise Exception(f"video {vid_path} has no frames")
            break
    vid = repeat_video(vid, l)

    vidcap.release()
    if form == 'tens': return TensorVideo(vid.stack().permute(3,0,1,2))
    else: return vid.map(PILImage.create)


class createVideoForm(Transform):
    '''Create a TensorVideo using form=tens or a list of PIL images using form=img '''
    def __init__(self, l='all', skip=3, form='tens'):
        self.l = l
        self.skip = skip
        self.form = form

    def encodes(self, vid_path):
        if self.skip is None:
            self.skip = random.randint(1,4)
        if isinstance(vid_path, (pd.Series, pd.DataFrame)): pass

        return create_video(vid_path, l=self.l, skip=self.skip, form=self.form)


class RandomCrop(Transform):
    def __init__(self, size: tuple ):
        self.size = size
    def encodes(self, ts_vd):
        return T.RandomCrop(self.size)(ts_vd)

class RandomHFlip(Transform):
    def __init__(self, p ):
        self.p = p
    def encodes(self, ts_vd):
        return T.RandomHorizontalFlip(self.p)(ts_vd)
class RandomColorJitter(Transform):
    def __init__(self,brightness=0, contrast=0, saturation=0, hue=0):
          self.transform = T.ColorJitter(brightness= brightness, contrast=contrast, saturation=saturation, hue=hue)
    def encodes(self, ts_vid):
        return self.transform(ts_vid.permute(1,0,2,3)).permute(1,0,2,3)