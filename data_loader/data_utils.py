#!/usr/bin/env python
# -*- coding=utf-8 -*-
from datetime import datetime
import re
import networkx as nx
import torch
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from torch_geometric.utils.convert import from_networkx


class CEBAFGraph(object):
    '''the class for a single cebaf graph, it stores the graph in a nx.Graph() object'''
    def __init__(self, node, link, info, meta, dt, directed=False):
        '''init a cebaf graph'''
        self.total_num = None
        self.node_type = {}
        self._parse_meta(meta)
        self._parse_info(info)
        self.directed=directed
        self.graph = self._parse_node_and_link(node, link)
        self.time = dt

        # also return a pd.Series
        d = {}
        for n in self.graph.nodes():
            d[self.graph.nodes()[n]['name']] = self.graph.nodes()[n]['attr']
        self.df = pd.DataFrame(data=[[self.time] + list(d.values())],  columns=['timestamp']+list(d.keys()))

    def _parse_meta(self, meta):
        '''parse meta data, contains total # of nodes, and # of node from each type'''
        pattern = re.compile('\d+')
        with open(meta) as f:
            for idx, line in enumerate(f):
                if idx == 0:
                    self.total_num = eval(pattern.findall(line)[0])
                else:
                    class_num = eval(pattern.findall(line)[-1])
                    self.node_type[idx-1] = {'num': class_num}
    
    def _parse_info(self, info):
        '''parse info, contains the name for the node type, and the name for attrs'''
        pattern = re.compile('\s+')
        with open(info) as f:
            for idx, line in enumerate(f):
                if idx == 0: continue
                t, n, l = pattern.split(line.strip())
                self.node_type[eval(t)]['name'] = n
                self.node_type[eval(t)]['labels'] = l.split(',')

    def _parse_node_and_link(self, node, link):
        '''parse node and link list, store the information in a nx.Graph'''
        if self.directed:
            g=nx.DiGraph()
        else:
            g = nx.Graph()
        df = pd.read_csv(node, sep='\t')
        edge_type = []
        for _, row in df.iterrows():
            attr = []
            for v in row['VALUES'].strip().split(','):
                try:
                    attr.append(eval(v))
                except Exception:
                    attr.append(np.nan)
            g.add_node(row['NODE'], name=row['NAME'].strip(), node_type=row['TYPE'], attr=attr)

        df = pd.read_csv(link, sep='\t')
        for _, row in df.iterrows():
            g.add_edge(row['START'], row['END'], edge_type=row['LINK_TYPE'], weight=row['LINK_WEIGHT'])

        return g

    def draw_graph(self):
        pos = nx.circular_layout(self.graph, scale=2)
        class2nodes = {}
        for k, v in nx.get_node_attributes(self.graph, 'node_type').items():
            class2nodes[v] = class2nodes.get(v, []) + [k]
        class2edges = {}
        for k, e in nx.get_edge_attributes(self.graph, 'edge_type').items():
            class2edges[e] = class2edges.get(e, []) + [k]
        fig, ax = plt.subplots(figsize=(50, 50))
        cmap = plt.get_cmap('tab20')
        # draw nodes, color indicates type
        for idx, nodes in enumerate(class2nodes.values()):
            nx.draw_networkx_nodes(self.graph, pos, nodes, node_shape='o', node_size=40, ax=ax,
                                   node_color=np.array(cmap.colors[idx]).reshape(1, -1))
        # draw edges, color indicates type
        for idx, edges in enumerate(class2edges.values()):
            nx.draw_networkx_edges(self.graph, pos, edges, width=.5, ax=ax,
                                   edge_color=np.array(cmap.colors[idx]).reshape(1, -1))

    def _to_pyg(self):
        # first convert to standard data
        data = from_networkx(self.graph)
        # data = data.to_heterogeneous()
        for i in range(len(data.attr)):
            data.attr[i] = torch.nan_to_num(torch.tensor(data.attr[i]))
        return data

    def _to_tensor(self):
        # flatten the graph to a huge vector
        vec = []
        node_attrs = nx.get_node_attributes(self.graph, 'attr')
        for attr in node_attrs.values():
            vec.extend(attr)
        vec = np.nan_to_num(np.array(vec))
        return torch.tensor(vec, dtype=torch.float32)

    def change_node_attr(self, node, new_attr):
        node_attr = self.graph.nodes[node]
        node_attr['attr'] = new_attr
        nx.set_node_attributes(self.graph, {node: node_attr})

    def __repr__(self):
        return 'CEBAF graph at %s with %d nodes and %d node types' % (
            datetime.strftime(self.time, '%m-%d-%Y %H:%M'), self.total_num, len(self.node_type)
        )

    @property
    def num_nodes(self):
        return self.graph.number_of_nodes()
 
    @property
    def num_edges(self):
        return self.graph.number_of_edges()

    @property
    def num_node_types(self):
        return len(self.node_type)

    # save the graph as a matrix
    # only the feature matrix needs to change


if __name__ == '__main__':
    g = CEBAFGraph('data/2021/04/26/17/node.dat',
                   'data/2021/04/26/17/link.dat',
                   'data/2021/04/26/17/info.dat',
                   'data/2021/04/26/17/meta.dat',
                    None)
    g._to_pyg()