import torch.nn as nn
import torch
from torchvision import models
from utils import save_net,load_net
import torch.nn.functional as F
import torchvision

class CSRNet(nn.Module):
    def __init__(self, load_weights=False):
        super(CSRNet, self).__init__()
        self.seen = 0
        self.frontend_feat = [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512]
        self.backend_feat  = [512, 512, 512,256,128,64]
        self.frontend = make_layers(self.frontend_feat)
        self.backend = make_layers(self.backend_feat,in_channels = 512,dilation = True)
        self.output_layer = nn.Conv2d(64, 1, kernel_size=1)
        if not load_weights:
            vgg = models.vgg16(pretrained = True)
            vgg_dict= vgg.state_dict()
            front_dict = self.frontend.state_dict()
            #self._initialize_weights()
            model_dict = []
            for key in front_dict:
               model_dict.append("features."+ key)
            # 1. filter out unnecessary keys
            vgg_dict = {k: v for k, v in vgg_dict.items() if k in model_dict}
            
            vgg_dict_update = {}
            for key in vgg_dict.keys():
                splits = key.split(".")
                newkey = splits[1] + "." + splits[2]
                vgg_dict_update[newkey] = vgg_dict[key] 
                
            # 2. overwrite entries in the existing state dict
            front_dict.update(vgg_dict_update)
            
            # 3. load the new state dict
            self.frontend.load_state_dict(front_dict)
        
            
    def forward(self,x):
        x = self.frontend(x)
        x = self.backend(x)
        x = self.output_layer(x)
        return x
        
    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.normal_(m.weight, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
                
def make_layers(cfg, in_channels = 3,batch_norm=False,dilation = False):
    if dilation:
        d_rate = 2
    else:
        d_rate = 1
    layers = []
    for v in cfg:
        if v == 'M':
            layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
        else:
            conv2d = nn.Conv2d(in_channels, v, kernel_size=3, padding=d_rate,dilation = d_rate)
            if batch_norm:
                layers += [conv2d, nn.BatchNorm2d(v), nn.ReLU(inplace=True)]
            else:
                layers += [conv2d, nn.ReLU(inplace=True)]
            in_channels = v
    return nn.Sequential(*layers)