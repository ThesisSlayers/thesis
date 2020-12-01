# AUTOGENERATED! DO NOT EDIT! File to edit: 07_read_video_function.ipynb (unless otherwise specified).

__all__ = ['show_frames', 'DF2Paths', 'Video', 'snippets_from_video', 'stretch', 'ResizeTime', 'encodes', 'TensorVideo',
           'encodes', 'encodes', 'UniformizedDataLoader', 'uniformize_dataset', 'UniformizedShuffle',
           'create_video_tensor']

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

# Cell
def show_frames(video,start=0, end=5):
    '''show frames in a video from start to end'''
    for frame in video[start:end]:
        clear_output(wait=True)
        frame.show()
        time.sleep(0.5)

class DF2Paths():
    def __init__(self, path, fps=24):
        self.path, self.fps = path, fps

    def __call__(self, item:pd.Series):
        def fr(t): return int(float(t)*self.fps)

        Id, start, end = item['id'], item['start'], item['end']
        start, end = fr(start), fr(end)
        step = -1 if start > end else 1                     # If start is greater than end,
                                                            # it reverses the order of the for loop
        vid = L()                                           # This because it seems some videos are in reverse
        for n in range(start, end, step):
            fr_path = self.path/'Charades_v1_rgb'/Id/f'{Id}-{n:0>6d}.jpg'
            if os.path.exists(fr_path):
                vid.append(fr_path)
        return vid

# Cell
@patch
def insert(l:L, i, o):
    l.items.insert(i, o)

class Video(L):
    @classmethod
    def create(cls, paths:(L,list,str), sep='\n'):
        '''create images from frames path in a video'''
        paths = paths.split(sep) if isinstance(paths, str) else paths
        return cls(map(PILImage.create, paths))

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
class TensorVideo(TensorBase): pass

@ToTensor
def encodes(self, vid:Video):
    return TensorVideo(vid.stack().permute(3,0,1,2))

# Cell
@IntToFloatTensor
def encodes(self, vid:TensorVideo):
    return vid.float()/self.div

# Cell
@delegates()
class UniformizedDataLoader(TfmdDL):
    def __init__(self, dataset=None, n_el=4, n_lbl=4, **kwargs):
        kwargs['bs'] = n_el*n_lbl
        super().__init__(dataset, **kwargs)
        store_attr(self, 'n_el,n_lbl')
        self.lbls = list(map(int, self.dataset.tls[1]))
        self.dl_vocab = list(range(len(self.vocab)))

    def before_iter(self):
        super().before_iter()
        lbl2idxs = {lbl:[] for lbl in self.dl_vocab}
        for i, lbl in enumerate(self.lbls): lbl2idxs[lbl].append(i)

        if self.shuffle: [random.shuffle(v) for v in lbl2idxs.values()]
        self.lbl2idxs = lbl2idxs

    def get_labeled_elements(self, lbl, n_el):
        els_of_lbl = []
        while len(els_of_lbl) < n_el:
            item = self.do_item(self.lbl2idxs[lbl].pop())
            if item is not None: els_of_lbl.append(item)
        return els_of_lbl

    def create_batches(self, samps):
        n_lbl, n_el = self.n_lbl, self.n_el
        self.it = iter(self.dataset) if self.dataset is not None else None

        while len(self.dl_vocab) >= n_lbl:

            batch_lbls, b = [], []

            while len(batch_lbls) < n_lbl:
                try: i = random.randint(0, len(self.dl_vocab) - 1)
                except ValueError: raise CancelBatchException
                lbl = self.dl_vocab.pop(i)
                if len(self.lbl2idxs[lbl]) < n_lbl: continue

                try: els_of_lbl = self.get_labeled_elements(lbl, n_el)
                except IndexError: continue

                b.extend(els_of_lbl)
                batch_lbls.append(lbl)

            self.dl_vocab.extend(batch_lbls)

            yield self.do_batch(b)

        self.dl_vocab = list(range(len(self.vocab)))

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
    return getattr(items, 'iloc', items)[idxs]

# Cell
class UniformizedShuffle():
    def __init__(self, lbls, vocab=None, n_el=4, n_lbl=4):
        self.lbls = lbls
        if vocab is None: vocab = list(set(lbls))
        self.vocab = vocab
        self.n_el = n_el
        self.n_lbl = n_lbl
    def __call__ (self, items):
        return uniformize_dataset(items, lbls=self.lbls, vocab=self.vocab, n_el=self.n_el, n_lbl=self.n_lbl)

# Cell
import torch
import torch.nn as nn
from fastai.vision.all import *
from fastai.data.all import *
from fastai.distributed import *
import pandas as pd
from pathlib import Path
import time
from video_block import *
from inflator import *
from triplet_loss import *

# Cell
import cv2
import random

# Cell
def create_video_tensor(vid_path, l=50, skip=3):
    vid = cv2.VideoCapture(str(vid_path))
    duration = vid.get(cv2.CAP_PROP_FRAME_COUNT)

    vid_tens, block = L(), l*skip
    start, i = random.randint(0,duration - block), 0
    while len(vid_tens) < l:
        vid.set(cv2.CAP_PROP_POS_FRAMES, start + i*skip)
        res, frame = vid.read()
        if res: vid_tens.append(frame)
        i += 1

    vid.release()
    return vid_tens.stack()
