from collections import namedtuple
from itertools import izip_longest

from analysis import LSAAnalyser
from parse import parse
from consts import *
import machine
from mtable import build_table, jk, minimize, generate_formula_args

def s_operation(name, elementary, infix, options, *args, **kwargs):
    nt = namedtuple(name + "_s", *args, **kwargs)
    lname = options['operator']
    def new_str(self):
        if elementary:
            fmt = ', '.join("%r" for i in range(len(self)))
            return "%s%s" % (lname, fmt) % self
        else:
            if infix:
                lst = [repr(r) for r in self[0]]
                ret = (' %s ' % lname).join(lst)
                if len(self[0]) > 1:
                    ret = "(%s)" % ret
                return ret
            else:
                return "%s(%s)" % (lname, ' '.join([repr(r) for r in self[0]]))
            
    nt.__repr__ = new_str
    return nt

andf = s_operation("and", False, True, {'operator':r"AND"}, ['args'])
orf = s_operation("or", False, True, {'operator':r"OR"}, ['args'])
notf = s_operation("not", False, False, {'operator':r"NOT"}, ['args'])
leQ = s_operation("Q", True, False, {'operator':"q_synt"}, ["id"])
leX = s_operation("X", True, False, {'operator':"x"}, ["id"])
leY = s_operation("Y", True, False, {'operator':"y"}, ["id"])


document = """
LIBRARY ieee;
USE ieee.std_logic_1164.all; 

LIBRARY work;

ENTITY Custom_FSM IS
	PORT
    (
clk :  IN  STD_LOGIC;
{ports}
    );
END Custom_FSM;

ARCHITECTURE Custom_FSM_Architecture OF Custom_FSM IS 

{internal_sigs}

BEGIN

{y_outs}
{processes}

END Custom_FSM_Architecture;
"""

process = """
PROCESS(clk)
VARIABLE synt_var_{sig} : STD_LOGIC;
BEGIN
IF (RISING_EDGE(clk)) THEN
	synt_var_{sig} := (NOT(synt_var_{sig}) AND (  
        {j_input}  
        )) OR (NOT(  
        {k_input}  
        ) AND (synt_var_{sig}));
END IF;
{sig} <= synt_var_{sig};
END PROCESS;
"""

port = "{sig} :  {dir}  STD_LOGIC{end}"
signal = "SIGNAL {sig} :  STD_LOGIC;"
y_out = "{sig} <= {formula};"

def _orf(args):
    if len(args) > 3:
        iters = [args.__iter__()]*3
        args = list(izip_longest(*iters, fillvalue="1"))
        return _orf(args=[orf(args=arg) for arg in args])
    elif len(args) == 1 or len(args) == 3:
        return orf(args=args)
    else:
        return orf(args=args + ["1"] * (3 - len(args)))



def generate_formula_vhdl(conditions):
    lst = []
    for simple in conditions:
        slst = []
        for c in simple:
            opf = None
            if c.name == 'q':
                op = lambda args: leQ(id=args)
            elif c.name == 'X':
                op = lambda args: leX(id=args)
            
            if c.val != 0:  # inverse all simples
                opf = lambda args: notf(args=[op(args)])
            else:
                opf = op
            slst.append(opf(c.index))
        if len(slst) == 1:
            if type(slst[0]) is notf:
                lst.append( _orf(slst[0].args) )
            else:
                lst.append( notf(args=slst) )
        else:
            lst.append( notf(args=[_orf(args=slst)]) )
    return _orf(args=lst)


def vhdl(jks, inputs, outputs):
    q_count = len(jks[0])
    js = [generate_formula_vhdl(minimize(jk, q_count, inputs)) for i, jk in enumerate(jks[0])]
    ks = [generate_formula_vhdl(minimize(jk, q_count, inputs)) for i, jk in enumerate(jks[1])]
    ys = [generate_formula_vhdl(minimize(jk, q_count, inputs)) for i, jk in enumerate(jks[2])]

    signals = [port.format(sig="x{}".format(x+1), dir="IN", end=";") for x in range(inputs)] + \
              [port.format(sig="y{}".format(x+1), dir="OUT", end=";" if (x+1) < outputs else "") for x in range(outputs)]

    internal_sigs = [signal.format(sig="q_synt{}".format(x)) for x in range(len(jks[0]))]

    y_outs = [y_out.format(sig="y{}".format(x+1), formula=ys[x]) for x in range(len(ys))]

    processes = [process.format(sig="q_synt{}".format(x), j_input=js[x], k_input=ks[x]) for x in range(len(js))]

    return document.format(
                        ports="\n".join(signals),
                        internal_sigs="\n".join(internal_sigs),
                        y_outs="\n".join(y_outs),
                        processes="\n".join(processes))


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\xb9Y\u2081X\u2082\u2191\xb2Y\u2082\u2193\xb9Y\u2083\u2193\xb2Y\u2084\u25cf'
    p = LSAAnalyser(parse(s))
    p.analysis()
    conn, sigs = machine.make_machine(p.matrix, p.barenodes)
    mc = machine.encode_machine(conn, sigs)
    tbl = build_table(*mc)
    jks = jk(tbl)

    # ks = [generate_formula("K_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    js = [generate_formula_vhdl(jk) for i, jk in enumerate(jks[0])]
    ks = [generate_formula_vhdl(jk) for i, jk in enumerate(jks[1])]
    # ys = [generate_formula("Y_{%d}" % (i), jk) for i, jk in enumerate(jks[1])]
    # print js
    # print js
    print p.in_signals
    vhdl(jks, len(p.in_signals), len(p.out_signals))
