from analysis import LSAAnalyser
from parse import parse
from consts import Signal #, CYCLE_NODE, ppi as _ppi
from functools import partial
from math import log, ceil

def negative(lst):
    return [Signal(name=l.name, index=l.index, inverted=not l.inverted) for l in lst]

def make_machine(table, signals):
    conn = []
    sigs = {0: []}

    # ppi = partial(_ppi, matrix=table)
    end_id = max(signals.keys())
    ppi = lambda x: x if x+1 != end_id else 0

    def _make_machine(start, prev, cond, visited):
        # print start, prev, cond
        line = table[start]
        no_deep = False
        targets = filter(lambda x: x[1] is not None, enumerate(line))
        is_cond = len(targets) > 1
        if not is_cond:
            if prev is not None:
                s = ( ppi(prev), ppi(start), cond )
                if s not in conn:
                    conn.append( s )
                else:
                    no_deep = True
                sigs[ppi(start)] = signals[start+1].node.signals
            #
            if not no_deep:
                for i,c in targets:
                    _make_machine(i, start, [], visited + [(start, is_cond)])
        else:
            it = (start, is_cond)
            if it in visited and all([m[1] for m in visited[visited.index(it):]]):
                print visited
                return
            for i,c in targets:
                s = signals[start+1].node.signals
                if not c:
                    s = negative(s)
                _make_machine(i, prev, cond + s, visited + [(start, is_cond)])
    _make_machine(0, None, [], [])
    return sorted(conn), sigs

def bit_exchanges(src, first=None):
    dst = bytearray(src)
    lst = range(len(src))
    if first:
        lst = sorted(list(set(lst).difference(set(first))), reverse=True)
        lst = first + lst
    print "exchanging ",src,"by",lst
    for i in lst:
        c = src[i]
        ret = dst[:]
        ret[i] = '0' if c == '1' else '1'
        yield str(ret)

class NotEnoughDigits(Exception):
    pass

def code_diff(a, b):
    return [x[0] for x in enumerate(zip(a, b)) if x[1][0]!=x[1][1] ]

def is_near(a, b):
    return len(code_diff(a,b)) <= 1

def encode_machine(table_src, signals_src):
    table = None
    signals = None
    digits = int(ceil(log(len(signals_src.keys()), 2)))
    success = False


    def encode(near, encoded, lst=None):
        possibles = filter(lambda code: code not in encoded.values(), bit_exchanges(near, lst))
        if possibles:
            return possibles[0]
        else:
            raise NotEnoughDigits()

    def _encode_machine():
        encoded = {0: "0"*digits}

        def _encode_vertex(vertex):
            near = [v[1] for v in table if v[0] == vertex] + [v[0] for v in table if v[1] == vertex]
            print "near %d: " % vertex, near
            not_encoded = [v for v in near if v not in encoded]
            print not_encoded
            for i in not_encoded:
                encoded[i] = encode(encoded[vertex], encoded)
                print "%d encoded with %s" % (i, encoded[i])
            for i in not_encoded:
                _encode_vertex(i)

        _encode_vertex(0)
        return encoded

    def insert_in_middle(i, conn):
        del table[i]
        new_index = max(signals.keys())+1
        signals[new_index] = []
        table.append((conn[0], new_index, conn[2]))
        table.append((new_index, conn[1], []))
        return new_index

    def _resolve_conflicts(encoded):
        added = []
        print "Resolving conflicts:", encoded
        no_conflicts = False
        while not no_conflicts:
            for i,conn in reversed(list(enumerate(table))):
                if not is_near(encoded[conn[0]], encoded[conn[1]]):
                    print "Conflict in", conn, ":", encoded[conn[0]], encoded[conn[1]]
                    new_index = insert_in_middle(i, conn)
                    encoded[new_index] = encode(encoded[conn[0]], encoded, code_diff(encoded[conn[0]], encoded[conn[1]]))
                    added.append(new_index)
                    print " . resolved with adding ", encoded[new_index]
                    break
            else:
                no_conflicts = True
        return encoded, added

    encoded = None
    while not success:
        try:
            print "======================"
            print "encoding, %d digits:" % digits
            encoded = None
            table = table_src[:]
            signals = signals_src.copy()
            encoded = _encode_machine()
            print encoded
            encoded, added = _resolve_conflicts(encoded)
            success = True
        except NotEnoughDigits:
            digits += 1
            print "NotEnoughDigits: Added digits, now %d" % digits

    return table, signals, encoded, added


def to_dict(machine):
    p1, p2, p3, p4 = machine
    p1_r = []
    for p in p1:
        p1_r.append([p[0], p[1], [{"index":x[1], "inv":x[2]} for x in p[2]] if p[2] else None ])
    # print p2
    p2_r = {}
    for k,v in p2.iteritems():
        p2_r[k] = v[0][1] if len(v) else None
    return {"connections":p1_r, "values":p2_r, "codes": p3, "additional_nodes": p4}

def from_dict(machine):
    p1 = machine['connections']
    p2 = machine['values']
    p3 = machine['codes']
    p4 = machine['additional_nodes']
    p1_r = []
    p2_r = {}
    for s in p1:
        p1_r.append((s[0], s[1], [Signal(u'X', x['index'], x['inv']) for x in s[2]] if s[2] else [] ))
    for k,v in p2.iteritems():
        p2_r[k] = [Signal(u'Y', v, False)] if v else []
    return (p1_r, p2_r, p3, p4)

if __name__ == '__main__':
    s = u'\u25cbY\u2081Y\u2082Y\u2083Y\u2084\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    print "===="
    for x in p.matrix:
        print x
    print "===="
    conn, sigs = make_machine(p.matrix, p.barenodes)
    print conn, sigs
    # import graph
    # graph.draw_machine(conn, sigs)

    # import yaml
    # print (conn, sigs)
    # # print 
    # y = yaml.dump(to_dict((conn, sigs)), default_flow_style=False)
    # print y
    # print
    # # print y
    # print from_dict(yaml.load(y))
    a = encode_machine(conn, sigs)
    d = to_dict(a)
    print a
    print a == from_dict(d)
