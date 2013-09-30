from analysis import LSAAnalyser
from parse import parse
from consts import Signal

def negative(lst):
    return [Signal(name=l.name, index=l.index, inverted=not l.inverted) for l in lst]

def make_machine(table, signals):
    conn = []
    sigs = {0: []}
    def _make_machine(start, prev, cond, visited):
        # print start, prev, cond
        line = table[start]
        no_deep = False
        targets = filter(lambda x: x[1] is not None, enumerate(line))
        is_cond = len(targets) > 1
        if not is_cond:
            if prev is not None:
                s = ( prev, start, cond )
                if s not in conn:
                    conn.append( s )
                else:
                    no_deep = True
                sigs[start] = signals[start+1].node.signals
            #
            if not no_deep:
                for i,c in targets:
                    _make_machine(i, start, [], visited + [start])
        else:
            if start in visited:
                return
            for i,c in targets:
                s = signals[start+1].node.signals
                if not c:
                    s = negative(s)
                _make_machine(i, prev, cond + s, visited + [start])
    _make_machine(0, None, [], [])
    return sorted(conn), sigs

def to_dict(machine):
    res = []
    if type(x) is dict:
        for i,x in machine.iteritems():
            if hasattr(x, '__iter__'):
                res.append(to_dict(x))
            else:
                res.append(str(x) if type(x) is unicode else x)
    else:
        for x in machine:
            if hasattr(x, '__iter__'):
                res.append(to_dict(x))
            else:
                res.append(str(x) if type(x) is unicode else x)
    return res

def from_dict(machine):
    print machine
    return machine[0]


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\xb9Y\u2081\u2191\xb2\u2193\xb9Y\u2082\u2193\xb2\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    print "===="
    for x in p.matrix:
        print x
    print "===="
    conn, sigs = make_machine(p.matrix, p.barenodes)
    # print conn, sigs
    # import graph
    # graph.draw_machine(conn, sigs)
    import yaml
    print (conn, sigs)
    y = yaml.dump(to_dict((conn, sigs)))
    print y
    print from_dict(yaml.load(y))
