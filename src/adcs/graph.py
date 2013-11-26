import analysis
import parse
from consts import *

import pydot

def draw_graph(nodes, connections, matrix, loop, renumerated):
    if renumerated is None:
        renumerated = {}
    if loop is None:
        loop = []
    print connections
    renumerated[max(renumerated.keys())+1] = 1
    G = pydot.Dot('graphname', graph_type='digraph', rankdir='TB', size=100)
    subg = pydot.Subgraph('', rank='same')
    G.add_subgraph(subg)
    print ">>>!!!"
    def prefix(k):
        prefix = "?"
        print renumerated, k
        if k in renumerated:
            prefix = "Z%d" % renumerated[k]
        return prefix

    print nodes
    for k,node in nodes.iteritems():
        outputs = len(filter(lambda x: x is not None, matrix[k-1]))
        # print outputs
        
        if outputs <= 1:
            G.add_node(pydot.Node(nodename(k, {k:node}), xlabel=prefix(k), shape='box'))
        else:
            G.add_node(pydot.Node(nodename(k, {k:node}),  shape='diamond'))

    for conn in connections:
        if conn[0]-1 in loop and conn[1]-1 in loop:
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

def renumerate(connections):
    numbers = Numerator()
    for conn in connections:
        numbers.get_id(conn[0]+1)
        numbers.get_id(conn[1]+1)

    return numbers

def draw_machine(connections, signals, codes=None, added=None):
    if not added:
        added = []
    print ">>>", signals
    G = pydot.Dot('graphname', graph_type='digraph', rankdir='LR', size=100)
    subg = pydot.Subgraph('', rank='same')
    G.add_subgraph(subg)

    numbers = renumerate(connections)
    all_nodes = set()
    for conn in connections:
        n1 = nodename_signal(signals.get(conn[0]), numbers.get_id(conn[0]+1))
        n2 = nodename_signal(signals.get(conn[1]), numbers.get_id(conn[1]+1))
        all_nodes.add((conn[0], n1))
        all_nodes.add((conn[1], n2))
        pair =(n1, n2)
        if not conn[2]:
            G.add_edge(pydot.Edge(*pair))
        else:
            G.add_edge(pydot.Edge(*pair, label=conditionname(conn[2])))

    print all_nodes
    print codes
    for i,name in all_nodes:
        if i in added:
            G.add_node(pydot.Node(name, xlabel=codes[i], style="dashed"))
        else:
            G.add_node(pydot.Node(name, xlabel=codes[i]))

    G.write_png('machine.png')
    print "image write"


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = analysis.LSAAnalyser(parse.parse(s))
    p.analysis()
    print p.connections
    print p.barenodes
    print
    draw_graph(p.barenodes, p.connections, p.matrix, None, None)
