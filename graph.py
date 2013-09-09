import analysis
import parse
from consts import *

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib

def draw_graph(nodes, connections, ax=None):
    G=nx.DiGraph()

    labels = {}
    for conn in connections:
        pair = nodename(conn[0], nodes), nodename(conn[1], nodes)
        G.add_edge(*pair,
            condition=conn[2])
        labels[pair] = conditionname(conn[2])

    matplotlib.rc('font', **{'family':'serif','serif':['Computer Modern']})
    pos = nx.graphviz_layout(G, prog='dot', args='-Nfontsize=10 -Nwidth=".2" -Nheight=".2" -Nmargin=0 -Gfontsize=10')
    # pos = nx.spring_layout(G, iterations=10)
    print "OK"
    nx.draw(G,pos,node_size=1600,alpha=0.6,with_labels=True,edge_color='b',node_color='y',font_size=13,node_shape='s',ax=ax)
    nx.draw_networkx_edge_labels(G, pos, labels, label_pos=0.5,rotate=False,ax=ax)


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = analysis.LSAAnalyser(parse.parse(s))
    p.analysis()
    print p.connections
    print p.barenodes
    print
    draw_graph(p.barenodes, p.connections)
