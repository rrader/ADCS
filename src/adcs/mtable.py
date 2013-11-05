import os

from analysis import LSAAnalyser
from parse import parse
from consts import *
import machine
from functools import partial
from collections import namedtuple
from latexmath2png import latexmath2png
import itertools
import operator

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


def is_conform(reqs, q, signals, reverse=False):
    ok = True
    lst = [condition(name='q', index=i, val=int(v)) for i,v in enumerate(q)] + \
          [condition(name='X', index=k, val=int(v)) for k,v in signals.iteritems()]
    if reverse:
        for q in reqs:
            ok = ok and any([it == q for it in lst])
    else:
        for q in lst:
            ok = ok and any([it == q for it in reqs])
    # if ok:
    #     print reqs, lst,
    return ok

# ===== minimization ======

def implicant_matrix(tbl, q, signals):
    matrix = []
    for item in ["".join(seq) for seq in itertools.product("01", repeat=q+signals)]:
        # print item
        q_it = item[:q]
        signals_it = {(k+1):v for k,v in enumerate(item[q:])}
        # print tbl, q_it, signals_it
        matrix.append((item, any([is_conform(it, q_it, signals_it, True) for it in tbl])))
    return matrix

def do_glue(pair):
    glued_1, glued_2, glued_res = [], [], []  # from list 1 or 2
    for x in pair[0]:
        for y in pair[1]:
            diff = machine.code_diff(x,y)
            if len(diff) == 1 and machine.code_stars(x) == machine.code_stars(y):
                glued = x, y
                glued_1.append(x)
                glued_2.append(y)
                impl = bytearray(x[:])
                impl[diff[0]] = "*"
                glued_res.append(str(impl))
    return glued_1 + glued_2, glued_res

def minimize(tbl, q, signals):
    num = q+signals
    print "====== minimization ======"
    matrix = implicant_matrix(tbl, q, signals)
    eq_1 = [x[0] for x in filter(lambda x: x[1], matrix)]
    group_cur = [filter(lambda x: x.count("1") == n, eq_1) for n in range(num+1)]
    glue = True
    implicants = []
    while group_cur:
        groups = []
        glued = []
        for i in zip(group_cur, group_cur[1:]):
            impl, glued_i = do_glue(i)
            glued += impl
            groups.append(glued_i)
        implicants = list(set(implicants + reduce(operator.add, group_cur)) - set(glued))
        group_cur = groups
    print implicants

    lst = {}
    for minterm in eq_1:
        lst[minterm] = [x for x in implicants if len(machine.code_diff(x, minterm, star=True)) == 0]
    simple = list(set(itertools.chain(*[v for i,v in lst.iteritems() if len(v) == 1])))
    not_simple = list(set(itertools.chain(*[v for i,v in lst.iteritems() if len(v) > 1])))

    ok = False
    index = 0
    while not ok:
        new_implicants = simple + not_simple[:index]
        for minterm in eq_1:
            if len([x for x in new_implicants if len(machine.code_diff(x, minterm, star=True)) == 0]) == 0:
                # no coverage
                index += 1
                break
        else:
            ok = True
        if index > len(not_simple):
            raise Exception("WTF")

    ret = []
    for item in new_implicants:
        cur_item = []
        for i, char in enumerate(item):
            if char != "*":
                if i < q:
                    cur_item.append(condition(name='q', index=i, val=int(char)))
                else:
                    cur_item.append(condition(name='X', index=i, val=int(char)))
        ret.append(cur_item)
    return ret


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\xb9Y\u2081Y\u2082\u2191\xb2\u2193\xb9Y\u2082\u2193\xb2\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    conn, sigs = machine.make_machine(p.matrix, p.barenodes)
    mc = machine.encode_machine(conn, sigs)
    print mc

    tbl = build_table(*mc)
    jks = jk(tbl)
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

        # j-s
        for char in jks:
            for item in char:
                for simple in item:  # or-items
                    ln.append('1' if is_conform(simple, t.q, signals) else '0')
        print ln
        # print t
    headers = ["Q%s" % i for i in range(len(tbl[0].q))] + \
              ["Q%s+1" % i for i in range(len(tbl[0].q))] + \
              ["X%d" % s.index for s in p.in_signals] + \
              ["Y%d" % s.index for s in p.out_signals] + \
              ["J%d" % i for i in range(len(tbl[0].q))] + \
              ["K%d" % i for i in range(len(tbl[0].q))]
    print headers

    print
    for x in jks:
        print "."
        for y in x:
            print y
    print
    print
    # js = [generate_formula("J_{%d}" % (i), jk) for i, jk in enumerate(jks[0])]
    for i,js in enumerate(jks[2]):
        # for ji in js:
        # print "J_%d" % i, "=", js
        print minimize(js, len(tbl[0].q), len(p.in_signals))
    # ks = [generate_formula("K_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    # ys = [generate_formula("Y_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    # print js
    # print ks
    # latexmath2png.math2png(js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks + js + ks, os.getcwd(), prefix = "adcs_")

