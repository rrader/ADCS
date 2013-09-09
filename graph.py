import analysis
import parse
from consts import *

import pydot
# import matplotlib.pyplot as plt
# import matplotlib

def draw_graph(nodes, connections):
    G = pydot.Dot('graphname', graph_type='digraph', rankdir='TB', size=100)
    subg = pydot.Subgraph('', rank='same')
    G.add_subgraph(subg)

    print nodes
    for k,node in nodes.iteritems():
        G.add_node(pydot.Node(nodename(k, {k:node})))

    # labels = {}
    for conn in connections:
        pair = nodename(conn[0], nodes), nodename(conn[1], nodes)
        if not conn[2]:
            G.add_edge(pydot.Edge(*pair))
        else:
            G.add_edge(pydot.Edge(*pair, label=conditionname(conn[2])))
        # labels[pair] = 

    # matplotlib.rc('font', **{'family':'serif','serif':['Computer Modern']})
    # pos = nx.graphviz_layout(G, prog='dot', args='-Nfontsize=10 -Nwidth=".2" -Nheight=".2" -Nmargin=0 -Gfontsize=10')
    # # pos = nx.spring_layout(G, iterations=10)
    # print "OK"
    # nx.draw(G,pos,node_size=1600,alpha=0.6,with_labels=True,edge_color='b',node_color='y',font_size=13,node_shape='s',ax=ax)
    # nx.draw_networkx_edge_labels(G, pos, labels, label_pos=0.5,rotate=False,ax=ax)
    # print G.edges()
    G.write_png('graph.png')
    print "image write"
    # graphWithPositions = pydot.graph_from_dot_data(G.create_dot())
    # print graphWithPositions


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = analysis.LSAAnalyser(parse.parse(s))
    p.analysis()
    print p.connections
    print p.barenodes
    print
    draw_graph(p.barenodes, p.connections)
