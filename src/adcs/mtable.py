import os

from analysis import LSAAnalyser
from parse import parse
from consts import *
import machine
from functools import partial
from collections import namedtuple
from latexmath2png import latexmath2png

table_item = namedtuple("table_item", ["q", "q2", "signals", "bit", "y"])
condition = namedtuple("condition", ["name", "index", "val"])

def s_operation(name, elementary, infix, latex, *args, **kwargs):
    nt = namedtuple(name + "_s", *args, **kwargs)
    lname = latex['operator']
    def new_str(self):
        if elementary:
            fmt = ', '.join("%r" for i in range(len(self)))
            return "%s_{%s}" % (lname, fmt) % self
        else:
            if infix:
                return (' %s ' % lname).join([repr(r) for r in self[0]])
            else:
                return "%s{%s}" % (lname, ' '.join([repr(r) for r in self[0]]))
            
    nt.__repr__ = new_str
    return nt

andf = s_operation("and", False, True, {'operator':r""}, ['args'])
orf = s_operation("or", False, True, {'operator':r"\vee"}, ['args'])
notf = s_operation("not", False, False, {'operator':r"\overline"}, ['args'])
leQ = s_operation("Q", True, False, {'operator':"Q"}, ["id"])
leX = s_operation("X", True, False, {'operator':"X"}, ["id"])
leY = s_operation("Y", True, False, {'operator':"Y"}, ["id"])


def build_table(connections, signals, codes, add):
    table = []
    for c in connections:
        bit = machine.code_diff(codes[c[0]], codes[c[1]])
        table.append(table_item(q=codes[c[0]], q2=codes[c[1]], signals=c[2], bit=bit, y=signals.get(c[0]))) # from, to, changed bit
    return table


def jk(tbl):
    triggers = len(tbl[0].q)
    print "Triggers count: ", triggers
    j = [[] for i in range(triggers)]
    k = [[] for i in range(triggers)]
    y = []
    for ln in tbl:
        print ln
        qc_l = [condition(name="q", index=i, val=int(v)) for i,v in enumerate(ln.q)]
        if ln.bit:
            qc = qc_l + [condition(name=s.name, index=s.index, val=0 if s.inverted else 1)
                         for s in ln.signals]
            if ln.q[ln.bit[0]] == '1':
                # kill
                k[ln.bit[0]].append(qc)
            else:
                # jump
                j[ln.bit[0]].append(qc)
        for ys in ln.y:
            if len(y) < ys.index:
                y += [[] for i in range(ys.index - len(y))]
            if qc_l not in y[ys.index-1]:
                y[ys.index-1].append(qc_l)
    return j,k,y

def generate_formula(pre, conditions):
    lst = []
    for simple in conditions:
        slst = []
        for c in simple:
            opf = None
            if c.name == 'q':
                op = lambda args: leQ(id=args)
            elif c.name == 'X':
                op = lambda args: leX(id=args)
            
            if c.val == 0:
                opf = lambda args: notf(args=[op(args)])
            else:
                opf = op
            slst.append(opf(c.index))
        lst.append(andf(args=slst))
    return "%s = %r" % (pre, orf(args=lst))


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\xb9Y\u2081Y\u2082\u2191\xb2\u2193\xb9Y\u2082\u2193\xb2\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    conn, sigs = machine.make_machine(p.matrix, p.barenodes)
    mc = machine.encode_machine(conn, sigs)
    print mc

    tbl = build_table(*mc)
    for t in tbl:
        ln = list(t.q) + list(t.q2)
        signals = {sx.index: not sx.inverted for sx in t.signals}
        for s in p.in_signals:
            if s.index in signals:
                ln.append(str(1 if signals[s.index] else 0))
            else:
                ln.append("-")
        ys = {sx.index: not sx.inverted for sx in t.y}
        for s in p.out_signals:
            if s.index in ys:
                ln.append(str(1 if ys[s.index] else 0))
            else:
                ln.append(str(0))
        print ln
        # print t
    headers = ["Q%s" % i for i in range(len(tbl[0].q))] + \
              ["Q%s+1" % i for i in range(len(tbl[0].q))] + \
              ["X%d" % s.index for s in p.in_signals] + \
              ["Y%d" % s.index for s in p.out_signals]
    print headers
    # for t in tbl:
    #     print t
    jks = jk(tbl)
    print jks
    js = [generate_formula("J_{%d}" % (i), jk) for i, jk in enumerate(jks[0])]
    ks = [generate_formula("K_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    ys = [generate_formula("Y_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    # print js
    print ks
    # latexmath2png.math2png(js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks, os.getcwd(), prefix = "adcs_")

