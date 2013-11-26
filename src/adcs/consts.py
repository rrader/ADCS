from collections import namedtuple
from functools import partial

# Nodes

Control = namedtuple('Control', ['type', 'signals'])
Signal = namedtuple('Signal', ['name', 'index', 'inverted'])
Node = namedtuple('Node', ['type', 'signals'])
Output = partial(Node, type='out')
Condition = partial(Node, type='in')
Jump = namedtuple('Jump', ['dir', 'index'])

CertainNode = namedtuple('CertainNode', ['id', 'nodeid', 'node'])


def nodename(node, nodes, num=None):
    n = nodes[node].node
    s = "%d." % (nodes[node].nodeid if num is None else num)
    if type(n) is Control:
        return s + n.type
    else:
        return s + ''.join([s.name + (str(s.index)) for s in n.signals])

def nodename_x(node, nodes):
    n = nodes[node].node
    s = "%d." % nodes[node].nodeid
    if type(n) is Control:
        return s + '-'
    else:
        return s + ''.join([s.name + (str(s.index)) for s in n.signals])

def nodename_n(n):
    if type(n) is Control:
        return n.type
    else:
        return ''.join([s.name + (str(s.index)) for s in n.signals])

def conditionname(cond, uncond=False):
    s = ''.join([('!' if s.inverted else '') + s.name + (str(s.index)) for s in cond])
    if uncond and not s:
        s = '+'
    return s

def conditionname_b(cond):
    if cond is None:
        value = '0'
    else:
        value = '1' if cond else '2'
    return value

def conditionname_t(cond):
    if cond is None:
        value = ''
    else:
        value = 'True' if cond else 'False'
    return value

def nodename_signal(signal, num):
    return "Z%d/%s" % (num, conditionname(signal) if signal else "")

# Unicode symbols

SUPERSCRIPT = {
    0: 0x2070,
    1: 0xB9,
    2: 0xB2,
    3: 0xB3,
    4: 0x2074,
    5: 0x2075,
    6: 0x2076,
    7: 0x2077,
    8: 0x2078,
    9: 0x2079,
}

SUPERSCRIPT_symbols = [unichr(x) for x in SUPERSCRIPT.values()]

SUBSCRIPT = {
    0: 0x2080,
    1: 0x2081,
    2: 0x2082,
    3: 0x2083,
    4: 0x2084,
    5: 0x2085,
    6: 0x2086,
    7: 0x2087,
    8: 0x2088,
    9: 0x2089,
}

SUBSCRIPT_symbols = [unichr(x) for x in SUBSCRIPT.values()]

def subscript_num(n):
    r = []
    for c in n:
        r.append(unichr(SUBSCRIPT[int(c)]))
    return ''.join(r)

ARROW_UP = unichr(0x2191)
ARROW_DOWN = unichr(0x2193)
SYMB_X = u"X"
SYMB_Y = u"Y"
GROUP_O = u"("
GROUP_C = u")"
SYMB_START = unichr(0x25CB)
SYMB_END = unichr(0x25CF)

INPUT_KEYS = {
    "w": ARROW_UP,
    "s": ARROW_DOWN,
    "x": SYMB_X,
    "y": SYMB_Y,
    "(": GROUP_O,
    ")": GROUP_C,
    "[": SYMB_START,
    "]": SYMB_END,
}

INPUT_KEYS.update(dict(((str(key), unichr(val)) for key, val in SUBSCRIPT.iteritems())))


class Numerator(dict):
    def get_id(self, num):
        # print "getting ", num
        # if num == CYCLE_NODE+1:
        #     return CYCLE_NODE+1  # start and end
        if not self.get(num):
            self.update({num: len(self) + 1})
        return self.get(num)
