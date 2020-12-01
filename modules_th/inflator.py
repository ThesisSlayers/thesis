# AUTOGENERATED! DO NOT EDIT! File to edit: 02_inflator.ipynb (unless otherwise specified).

__all__ = ['AdaptiveConcatPool3d', 'get_hps', 'inflate']

# Cell
import torch
import torch.nn as nn
import fastcore
from fastai.vision.all import *
from torchvision.models import resnet18
from torchvision.models import inception_v3
from torchvision.models import googlenet

# Cell
class AdaptiveConcatPool3d(nn.Module):
    def __init__(self, size=None):
        super().__init__()
        size = size or (1,1,1)
        self.ap = nn.AdaptiveAvgPool3d(size)
        self.mp = nn.AdaptiveMaxPool3d(size)
    def forward(self, x): return torch.cat([self.mp(x), self.ap(x)], 1)

# Cell
def get_hps(module):
    # Getting hyper parameter names
    hp_names = type(module).__init__.__code__.co_varnames[1:] # little trick that gets me the names of the
                                                              # inputs of the init function
    # Creating hyper parameter dict and Inflating tuple hps (kernel_size, padding, etc.)
    hps = {}
    for k in hp_names:
            v = getattr(module, k)
            hps[k] = ((v[0]+v[1])//2, *v) if isinstance(v, tuple) else v
    return hps

# Cell
@typedispatch
def inflate(c2d:nn.Conv2d):
    hps = get_hps(c2d)
    hps['bias'] = not hps['bias'] is None

    # Inflating the 2d params and storing them in state dict
    c3d = nn.Conv3d(**hps)
    sd = {'weight':c2d.weight.unsqueeze(2).expand(*c3d.weight.shape)}
    if hps['bias']: sd['bias'] = c2d.bias

    c3d.load_state_dict(sd, strict=False)
    return c3d

@typedispatch
def inflate(bn2d:nn.BatchNorm2d):
    bn3d = nn.BatchNorm3d(**get_hps(bn2d))
    bn3d.load_state_dict(bn2d.state_dict())
    return bn3d

@typedispatch
def inflate(do2d:nn.Dropout2d):
    p, inplace = do2d.p, do2d.inplace
    return nn.Dropout3d(p, inplace)

@typedispatch
def inflate(m:nn.MaxPool2d): return nn.MaxPool3d(**get_hps(m))

@typedispatch
def inflate(m:nn.AvgPool2d): return nn.AvgPool3d(**get_hps(m))

@typedispatch
def inflate(m:AdaptiveConcatPool2d): return AdaptiveConcatPool3d(**get_hps(m))

@typedispatch
def inflate(m:nn.AdaptiveAvgPool2d): return nn.AdaptiveAvgPool3d(**get_hps(m))

@typedispatch
def inflate(m:nn.AdaptiveMaxPool2d): return nn.AdaptiveMaxPool3d(**get_hps(m))

@typedispatch
def inflate(m:nn.Module):
    for name, child in m.named_children():
        setattr(m, name, inflate(child))
    return m

inflate = inflate