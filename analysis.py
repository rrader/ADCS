
from consts import *

from collections import namedtuple

Node = namedtuple('Node', ['name', 'index'])

STATE_START = "start"
STATE_END = "end"
STATE_EXPR_START = "exprstart"
STATE_X_READ = "X_?"
STATE_Y_READ = "Y_?"
STATE_UP_READ = "^_?"
STATE_DOWN_READ = "v_?"
STATE_GROUP_END = ")"

START_SYMBOLS = [SYMB_X, SYMB_Y, GROUP_O, GROUP_C, ARROW_DOWN, ARROW_UP]

class LSASyntaxError(Exception):
    pass


def assert_s(val, lst):
    if val not in lst:
        msg = u"%s not in %s" % (ord(val), [ord(x) for x in lst])
        raise LSASyntaxError(msg)

def assert_b(boolean, message="assertion failed"):
    if not boolean:
        raise LSASyntaxError(message)

def lca_machine():
    STATE = None
    INGROUP = False
    val = yield
    pushback = False
    ret = None
    grouped_node = None

    elementary_node_states = [STATE_X_READ, STATE_Y_READ, STATE_UP_READ, STATE_DOWN_READ]

    def return_value(node, state):
        if state in elementary_node_states:
            node_obj = Node(name=node[0], index=int(node[1:]))
            if INGROUP:
                grouped_node.append(node_obj)
                return None
            else:
                return node_obj
        elif state == STATE_GROUP_END:
            return grouped_node

    while True:
        if val == SYMB_END:
            ret = return_value(node, STATE)
            yield ret
            break

        elif STATE == None:
            # wait START
            assert_s(val, [SYMB_START])
            STATE = STATE_EXPR_START

        elif STATE == STATE_EXPR_START:
            assert_s(val, START_SYMBOLS)
            if val == SYMB_X:
                STATE = STATE_X_READ
            elif val == SYMB_Y:
                STATE = STATE_Y_READ
            elif val == ARROW_UP:
                STATE = STATE_UP_READ
            elif val == ARROW_DOWN:
                STATE = STATE_DOWN_READ
            elif val == GROUP_O:
                assert_b(INGROUP==False, "nested groups forbidden")
                INGROUP = True
                grouped_node = []
            elif val == GROUP_C:
                assert_b(INGROUP==True, "unexpected bracket")
                STATE = STATE_GROUP_END
                pushback = True
            node = val

        elif STATE == STATE_GROUP_END:
            ret = return_value(node, STATE)
            STATE = STATE_EXPR_START
            INGROUP = False

        elif STATE in elementary_node_states:
            assert_s(val, SUBSCRIPT_symbols + START_SYMBOLS)
            if val not in START_SYMBOLS:
                node += str(SUBSCRIPT_symbols.index(val))
            else:
                # end of reading signal
                ret = return_value(node, STATE)
                STATE = STATE_EXPR_START
                pushback = True

        if not pushback:
            val = yield ret
            ret = None

        pushback = False


def parse(src):
    machine = lca_machine()
    machine.next()
    parsed = []
    for n, s in enumerate(src):
        try:
            r = machine.send(s)
            if r:
                parsed.append(r)
        except LSASyntaxError, e:
            raise LSASyntaxError("at %d: " % n + e.message)
    return parsed

if __name__ == '__main__':
    try:
        print (parse(u'\u25cbX\u2081(Y\u2082Y\u2083)\u2191\u2083\u2193\u2083\u25cf'))
    except LSASyntaxError, e:
        print "Syntax error " + e.message
