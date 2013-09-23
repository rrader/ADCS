import analysis
import parse
from consts import *

import pydot

def draw_graph(nodes, connections, matrix, loop):
    G = pydot.Dot('graphname', graph_type='digraph', rankdir='TB', size=100)
    subg = pydot.Subgraph('', rank='same')
    G.add_subgraph(subg)

    print nodes
    for k,node in nodes.iteritems():
        outputs = len(filter(lambda x: x is not None, matrix[k-1]))
        print outputs
        if outputs <= 1:
            G.add_node(pydot.Node(nodename(k, {k:node}), shape='box'))
        else:
            G.add_node(pydot.Node(nodename(k, {k:node}), shape='diamond'))

    # labels = {}
    highlighted = []
    if loop:
        highlighted = zip(loop, loop[1:])
    for conn in connections:
        if (conn[0]-1, conn[1]-1) in highlighted:
            color = 'red'
        else:
            color = 'black'
        pair = nodename(conn[0], nodes), nodename(conn[1], nodes)
        outputs = len(filter(lambda x: x is not None, matrix[conn[0]-1]))
        if conn[2] is None or outputs <= 1:
            G.add_edge(pydot.Edge(*pair, color=color))
        else:
            G.add_edge(pydot.Edge(*pair, label=conditionname_t(conn[2]), color=color))

    G.write_png('graph.png')
    print "image write"


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = analysis.LSAAnalyser(parse.parse(s))
    p.analysis()
    print p.connections
    print p.barenodes
    print
    draw_graph(p.barenodes, p.connections, p.matrix)
