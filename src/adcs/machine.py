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

def to_dict(machine):
    p1, p2 = machine
    p1_r = []
    for p in p1:
        p1_r.append([p[0], p[1], [{"index":x[1], "inv":x[2]} for x in p[2]] if p[2] else None ])
    # print p2
    p2_r = {}
    for k,v in p2.iteritems():
        p2_r[k] = v[0][1] if len(v) else None
    return {"connections":p1_r, "values":p2_r}

def from_dict(machine):
    p1 = machine['connections']
    p2 = machine['values']
    p1_r = []
    p2_r = {}
    for s in p1:
        p1_r.append((s[0], s[1], [Signal(u'X', x['index'], x['inv']) for x in s[2]] if s[2] else [] ))
    for k,v in p2.iteritems():
        p2_r[k] = [Signal(u'Y', v, False)] if v else []
    return (p1_r, p2_r)

if __name__ == '__main__':
    s = u'\u25cb\u2193\xb3X\u2081\u2191\xb9X\u2082\u2191\xb2Y\u2081\u2191\xb3\u2193\xb2Y\u2082\u2191\u2074\u2193\xb9X\u2083\u2191\u2075Y\u2083\u2191\u2074\u2193\u2075Y\u2084\u2191\xb3\u2193\u2074\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    print "===="
    for x in p.matrix:
        print x
    print "===="
    conn, sigs = make_machine(p.matrix, p.barenodes)
    print conn, sigs
    import graph
    graph.draw_machine(conn, sigs)

    import yaml
    print (conn, sigs)
    # print 
    y = yaml.dump(to_dict((conn, sigs)), default_flow_style=False)
    print y
    print
    # print y
    print from_dict(yaml.load(y))
