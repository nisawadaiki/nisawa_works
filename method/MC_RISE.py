import numpy as np
import tensorflow as tf
from tqdm import tqdm
import pdb
import random
import matplotlib.pyplot as plt
import cv2


def processing_imagenet_image(image,masks,mask0,mean= [103.939, 116.779, 123.68]):
    mean = [103.939, 116.779, 123.68]
    sample = image+mean
    sample=np.where(sample>255,255,sample)
    sample=np.where(sample<0,0,sample)
    sample1 = cv2.cvtColor(sample[0].astype(np.uint8), cv2.COLOR_BGR2RGB)
    #pdb.set_trace()
    mask_image = mask0* sample1 + masks*255
    mask_image_bgr=[cv2.cvtColor(mask_image[i].astype(np.uint8), cv2.COLOR_RGB2BGR) for i in range(mask_image.shape[0])]
    stack = np.array(mask_image_bgr) - mean

    return stack

class Mc_Rise(tf.Module):
    def __init__(self, model,dataset, gpu_batch=500):
        super(Mc_Rise, self).__init__()
        self.model = model
        self.dataset = dataset
        self.gpu_batch = gpu_batch
    
    def load_masks(self, to_path,filepath,p1):
        self.masks = np.load(to_path+filepath)
        #バイアスマスクの作成
        sum_color_mask=np.where((np.sum(self.masks,axis=-1))>1,1,np.sum(self.masks,axis=-1))
        mask0 = 1 - sum_color_mask
        self.mask0 = np.expand_dims(mask0,axis=-1)
        
        self.N = self.masks.shape[0]
        self.p1 = p1
        return self.masks

    def forward(self, image):
        N = self.N
        image = np.expand_dims(image,axis=0)
        _,  H, W,C = image.shape[0],image.shape[1],image.shape[2],image.shape[3]
        #マスク画像の作成
        if self.dataset == 'GTSRB':
            stack = self.mask0*image + self.masks
        elif self.dataset == 'ImageNet':
            stack = processing_imagenet_image(image,self.masks,self.mask0)

        score_list = []
        for i in range(0, N, self.gpu_batch):
            score_list.append(self.model(stack[i:min(i + self.gpu_batch, N)]))
        score_list = np.concatenate(score_list)

        return score_list,self.masks,self.mask0
    
