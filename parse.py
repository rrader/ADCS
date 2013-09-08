
from consts import *

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
        if val:
            msg = u"%s not in %s" % (ord(val), [ord(x) for x in lst])
        else:
            msg = "empty input expected " + str([ord(x) for x in lst])
        raise LSASyntaxError(msg)

def assert_b(boolean, message="assertion failed"):
    if not boolean:
        raise LSASyntaxError(message)

def lca_machine():
    STATE = None
    INGROUP = False
    INGROUP_TYPE = [None]
    val = yield
    pushback = False
    ret = Control(type="Start")
    grouped_node = None

    elementary_node_states = [STATE_X_READ, STATE_Y_READ, STATE_UP_READ, STATE_DOWN_READ]

    def return_value(node, state):
        if state in [STATE_X_READ, STATE_Y_READ]:
            if state == STATE_X_READ:
                nodetype = Condition
            elif state == STATE_Y_READ:
                nodetype = Output

            assert_b(len(node) > 1 and node[1:].isdigit(), "no index at signal")
            signal = Signal(name=node[0], index=int(node[1:]), inverted=False)

            if INGROUP:
                grouped_node.append(signal)
                if not INGROUP_TYPE[0]:
                    INGROUP_TYPE[0] = nodetype
                else:
                    assert_b(INGROUP_TYPE[0] == nodetype, "combinations of signals not allowed")
                return None
            else:
                return nodetype(signals=[signal])

        elif state in [STATE_UP_READ, STATE_DOWN_READ]:
            assert_b(len(node) > 1, "no index at arrow")
            return Jump(dir=node[0], index=int(node[1:]))

        elif state == STATE_GROUP_END:
            return INGROUP_TYPE[0](signals=grouped_node)

    node = None
    while True:
        if val == SYMB_END:
            assert_b(node, "empty algorithm")
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
                INGROUP_TYPE[0] = None
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
            assert_s(val, SUBSCRIPT_symbols + SUPERSCRIPT_symbols + START_SYMBOLS)
            if val not in START_SYMBOLS:
                if val in SUBSCRIPT_symbols:
                    node += str(SUBSCRIPT_symbols.index(val))
                else:
                    node += str(SUPERSCRIPT_symbols.index(val))                   
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
    print "PARSING " + src
    for c in src:
        print c, ord(c)
    assert_b(len(src), "empty input")
    assert_b(src[0] == SYMB_START, "no start symbol")
    assert_b(src[-1] == SYMB_END, "no end symbol")
    machine = lca_machine()
    machine.next()
    parsed = []
    for n, s in enumerate(src):
        try:
            r = machine.send(s)
            if r:
                parsed.append(r)
        except LSASyntaxError, e:
            err = LSASyntaxError("at %d: " % n + e.message)
            err.pos = n
            raise err
        except StopIteration:
            err = LSASyntaxError("at %d: unexpected symbol" % n)
            err.pos = n
            raise err
    try:
        machine.next()
    except StopIteration:
        parsed.append(Control(type="End"))
    return parsed

if __name__ == '__main__':
    try:
        print (parse(u'\u25cbX\u2081(Y\u2082Y\u2083)\u2191\u2083\u2193\u2083\u25cf'))
    except LSASyntaxError, e:
        print "Syntax error " + e.message
