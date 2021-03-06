import torch
import torch.nn as nn
import numpy as np
import pdb
import matplotlib.pyplot as plt

# the neural net 

class Model(nn.Module):
    def __init__(self, L, Ncat, K, embd_size):
        super().__init__()

        # Decide which components are enabled
        self.hidden_size = hidden_size = K

        self.rnn = nn.LSTM(input_size=embd_size+L, hidden_size=hidden_size, batch_first=True)
        self.out_feats = nn.Linear(hidden_size, L)
        self.out_cats = nn.Linear(hidden_size, Ncat)
        self.embd = nn.Embedding(Ncat, embd_size)

    def forward(self, x, xcats): 

        xcat_embd = self.embd(xcats) 
        xin = torch.cat([x, xcat_embd], dim=2)

        hpreds, _ = self.rnn(xin)

        xhat = self.out_feats(hpreds)
        xcat_hat = self.out_cats(hpreds)

        return xhat, xcat_hat


def create_mask(labels, x):
    regions = [range(0, 6), range(6, 12), range(12, 18), range(18, 24)]

    mask = torch.zeros(x.shape)   # create a mask with shape of x

    for i, label_seq in enumerate(labels):
        for t, label in enumerate(label_seq):
            mask[i, t, regions[label]] = 1 

    return mask
    

###### generate example sequences 

BS = 1000
T = 100
Ncat = 4
L = 24

# what I am doing here is just an arbitrary way of generating sequences. 
xcats = torch.arange(Ncat).repeat(BS, T//4)
x = torch.ones(BS, T, L) 
x = x * xcats.unsqueeze(-1)

pdb.set_trace()

# instantiate the model 
mdl = Model(L, Ncat, K=100, embd_size=24)

optimizer = torch.optim.Adam(mdl.parameters(), lr=1e-3)

# create the model mask 
mask = create_mask(xcats, x).bool()

cr_ent = nn.CrossEntropyLoss() 

for epoch in range(100):

    ## predict the next step
    xhat, xcat_hat = mdl.forward(x[:, :-1, :], xcats[:, :-1]) 
    
    # compute categorical loss
    loss_categorical = cr_ent(xcat_hat.permute(0, 2, 1), xcats[:, 1:])
    
    # get the masks for next step
    mask_next = mask[:, 1:, :]   # next step
    x_next = x[:, 1:, :] 

    x_next_masked = torch.masked_select(x_next, mask_next)
    xhat_masked = torch.masked_select(xhat, mask_next)

    # compute the loss for the features 
    loss_features = (x_next_masked - xhat_masked).abs().mean()

    # the total loss is the sum of both
    loss_total = loss_features + loss_categorical

    optimizer.zero_grad()
    loss_total.backward()
    
    optimizer.step()

    print('total loss {}, categorical loss {}, feature loss {}, epoch {}'.format(loss_total.item(),
                                                                       loss_categorical.item(), loss_features.item(), epoch))


