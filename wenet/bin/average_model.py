# Copyright 2019 Mobvoi Inc. All Rights Reserved.
# Author: binbinzhang@mobvoi.com (Binbin Zhang)
import os
import argparse
import glob
import re

import yaml
import numpy as np
import torch

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='average model')
    parser.add_argument('--dst_model', required=True, help='averaged model')
    parser.add_argument('--src_path',
                        required=True,
                        help='src model path for average')
    parser.add_argument('--val_best',
                        action="store_true",
                        help='averaged model')
    parser.add_argument('--num',
                        default=5,
                        type=int,
                        help='nums for averaged model')

    args = parser.parse_args()
    print(args)
    checkpoints = []
    val_scores = []
    if args.val_best:
        yamls = glob.glob('{}/[!train]*.yaml'.format(args.src_path))
        loss_best = {}
        for y in yamls:
            with open(y, 'r') as f:
                dic_yaml = yaml.load(f)
                loss = dic_yaml['cv_loss']
                epoch = dic_yaml['epoch']
                val_scores += [[epoch, loss]]
        val_scores = np.array(val_scores)
        sort_idx = np.argsort(val_scores[:, -1])
        sorted_val_scores = val_scores[sort_idx][::1]
        print("best val scores = " + str(sorted_val_scores[:args.num, 1]))
        print("selected epochs = " +
              str(sorted_val_scores[:args.num, 0].astype(np.int64)))
        path_list = [
            args.src_path + '/{}.pt'.format(int(epoch))
            for epoch in sorted_val_scores[:args.num, 0]
        ]
    else:
        path_list = glob.glob('{}/[!avg][!final]*.pt'.format(args.src_path))
        path_list = sorted(path_list, key=os.path.getmtime)
        path_list = path_list[-args.num:]
    print(path_list)
    avg = None
    num = args.num
    assert num == len(path_list)
    for path in path_list:
        print('Processing {}'.format(path))
        states = torch.load(path, map_location=torch.device('cpu'))
        if avg is None:
            avg = states
        else:
            for k in avg.keys():
                avg[k] += states[k]
    # average
    for k in avg.keys():
        if avg[k] is not None:
            avg[k] /= num
    print('Saving to {}'.format(args.dst_model))
    torch.save(avg, args.dst_model)
