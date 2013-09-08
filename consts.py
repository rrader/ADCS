from collections import namedtuple
from functools import partial

# Nodes

Control = namedtuple('Control', ['type'])
Signal = namedtuple('Signal', ['name', 'index', 'inverted'])
Node = namedtuple('Node', ['type', 'signals'])
Output = partial(Node, type='out')
Condition = partial(Node, type='in')
Jump = namedtuple('Jump', ['dir', 'index'])

CertainNode = namedtuple('CertainNode', ['id', 'nodeid', 'node'])

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
