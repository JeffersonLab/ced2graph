#!/usr/bin/env python
# -*- coding=utf-8 -*-
import os
import pickle as pkl
from datetime import datetime
import pandas as pd
import multiprocessing as mp


from data_loader.data_utils import CEBAFGraph


class CEBAFGraphLoader(object):
    def __init__(self, start_datehour=None, end_datehour=None, data_path='./20221114_072052', directed=False):
        '''
        init the loader with the time range, from start_datehour to end_datehour,
        both included. data_path is the directory storing the graphs
        '''
        self.start = start_datehour
        self.end = end_datehour
        self.data_path = data_path
        self.time_steps = self._create_file_paths()
        self.file_names = ['node.dat', 'link.dat', 'info.dat', 'meta.dat']
        self.pickle_name = 'graph.pkl'
        self.datetime2id = {}
        self.graphs = []
        self.directed = directed

    def load_date(self, t):
        file_path = os.path.join(self.data_path, t)

        return CEBAFGraph(
            *[os.path.join(file_path, entry) for entry in self.file_names], t, self.directed)

    def load_graph(self):
        '''load graph files and create CEBAFGraph objective from them'''
        with mp.Pool() as pool:
            self.graphs = pool.map(self.load_date, self.time_steps)
        self.df = pd.concat(g.df for g in self.graphs)

    def _create_file_paths(self):
        '''examine how many graphs exist in this range, and load the path to their directory'''
        time_stamps=[]
        for dir_name in os.listdir(self.data_path):
            full_dir_name = os.path.join(self.data_path, dir_name)
            if (os.path.isdir(full_dir_name)):      # excludes config.yaml or other top-level files
                time_stamps.append(dir_name)
        return time_stamps

    def make_pickles(self):
        '''Save the pickled graph object to a file in the same directory with node.dat, link.dat, etc.'''
        i = 0
        for g in self.get_pyg_graphs():
            outdir = os.path.join(self.data_path, self.time_steps[i])
            outfile = os.path.join(outdir, self.pickle_name)
            pkl.dump(g, open(outfile, 'wb'))
            i += 1

    def get_pyg_graphs(self):
        for i in range(self.num_graphs):
            yield self.graphs[i]._to_pyg()

    def get_pyg_tensors(self):
        for i in range(self.num_graphs):
            yield self.graphs[i]._to_tensor()

    def __getitem__(self, idx):
        return self.graphs[idx]

    def __len__(self):
        return len(self.time_steps)

    def __repr__(self):
        return 'CEBAF graph loader, %d graphs in total'% (
            len(self.time_steps)
        )

    @property
    def start_time(self):
        return datetime.strftime(self.start, '%m-%d-%Y %H:%M')

    @property
    def end_time(self):
        return datetime.strftime(self.end, '%m-%d-%Y %H:%M')

    @property
    def num_graphs(self):
        return len(self.time_steps)


