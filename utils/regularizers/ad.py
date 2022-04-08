import torch
from torch.nn import functional as F
import numpy as np


def CAD(weight, theta):
    m = weight.shape[0]
    W = torch.cat((weight.view(m, -1), (-1)*weight.view(m, -1)), 0)
    return cad_function(W, theta)

def cad_function(W, theta):
    m = W.shape[0]
    WWT = W @ torch.t(W)
    norm = torch.diagonal(WWT, 0) 
    N = torch.sqrt(norm[:, None] @ norm[None, :]).detach()
    M = (WWT / N > np.cos(theta))*(WWT / N > 0)*(1 - torch.eye(m, dtype=float).cuda())

    tloss = torch.sum(((torch.arccos(WWT*M) - theta)*M)**2)
    nloss = torch.sum((1 - norm)**2)
    return nloss, tloss


def ADK(weight, theta):
    m = weight.shape[0]
    W = weight.view(m, -1)
    return cad_function(W, theta)


def ad_function(W, theta):
    m = W.shape[0]
    WWT = W @ torch.t(W)
    norm = torch.diagonal(WWT, 0)
    N = torch.sqrt(norm[:, None] @ norm[None, :]).detach() + 1e-8
    if theta == 1.5708:
        M = 1 - torch.eye(m, dtype=float).cuda()
        tloss = torch.sum(((torch.arccos(WWT*M) - theta)*M)**2)
    else:
        Z = (1 - torch.eye(m, dtype=float)).type(torch.bool)
        M1 = (WWT/N > np.cos(theta))*Z
        M2 = (WWT/N < -np.cos(theta))*Z
        tloss = torch.sum(((torch.arccos(WWT[M1]) - theta))**2) + \
            torch.sum(((torch.arccos(WWT[M2]) - 3.1416 + theta))**2)
    
    nloss = torch.sum((1 - norm)**2)
    return nloss, tloss


def ADC(kernel, theta, stride):
    [o_c, i_c, w, h] = kernel.shape
    padding = int(np.floor((w - 1)/stride)*stride)
    output = torch.conv2d(kernel, kernel, stride=stride, padding=padding)
    ct = int(np.floor(output.shape[-1]/2))
    norm = torch.sqrt(torch.diagonal(output[:, :, ct, ct], 0)).detach() 

    output2 = output / (norm[:, None] @ norm[None, :])[:, :, None, None]

    output2[output2 > 0] -= 1e-3
    output2[output2 < 0] += 1e-3

    output3 = torch.arccos(output2)

    M = torch.zeros((o_c, o_c, output.shape[-2], output.shape[-1])).cuda()
    M[:, : ,ct, ct] = torch.eye(o_c).cuda()
    
    nloss = torch.sum((output[M == 1] - 1)**2)

    if theta == 1.5708:
        tloss = torch.sum((output3[M == 0] - 1.5708)**2)
    else:
        M1 = (output3 < theta)*(M == 0)
        M2 = (output3 > 3.1416 - theta)*(M == 0)
        tloss = torch.sum((output3[M1] - theta)**2) + \
            torch.sum((output3[M2] - 3.1416 + theta)**2)
    return nloss, tloss


    