from consts import *
from parse import parse
from itertools import chain

class LSAAlgorithmError(Exception):
    pass

def assert_b(boolean, message="assertion failed"):
    if not boolean:
        print message
        raise LSAAlgorithmError(message)


class LSAAnalyser(object):
    def __init__(self, parsed):
        self.parsed = parsed

    def lca_machine(self):
        STATE = None
        val = yield
        pushback = False
        ret = None

        while True:
            if not pushback:
                val = yield ret
                ret = None

            pushback = False

    def signal_sanity_check(self, lst):
        indexes = {x.index for x in lst}
        if len(lst) == 0:
            return

        err = "indexes of %s signals should be consistent" % lst[0].name
        assert_b(min(indexes) == 1, err)
        assert_b(max(indexes) == len(indexes), err + " (some numbers missing)")

    def arrow_sanity_check(self, lst):
        indexes = {x.index for x in lst}
        if len(lst) == 0:
            return

        err = "indexes of %s arrows should be consistent" % ("UP" if lst[0].dir == ARROW_UP else "DOWN")
        assert_b(min(indexes) == 1, err)
        assert_b(max(indexes) == len(indexes), err + " (some numbers missing)")

    def _invert(self, signals):
        return [Signal(name=x.name, index=x.index, inverted=not x.inverted) for x in signals]

    def _make(self, start, stack, condition):
        if start >= len(self.enumerated): return
        if start == 0:
            self.connections = []
            self.connections_q = []

        # print "* ", start, stack

        curr = self.enumerated[start]
        if type(curr) is CertainNode:
            print ">> node. ", curr
            if len(stack):
                assert_b(type(stack[-1].node) is Control or stack[-1].node.type == 'out',
                    'expected jump after input node')
                if type(curr.node) is Control or curr.node.type == 'out':
                    print r"%%", (stack[-1], curr), condition
                    assert_b(((stack[-1].nodeid, curr.nodeid) not in self.connections_q) ==
                        ((stack[-1].nodeid, curr.nodeid, condition) not in self.connections),
                        "two ways from %s to %s" % (nodename_n(stack[-1].node), nodename_n(curr.node)))
                    self.connections.append((stack[-1].nodeid, curr.nodeid, condition))
                    self.connections_q.append((stack[-1].nodeid, curr.nodeid))
                    stack.pop()
            self._make(start + 1, stack + [curr], [])

        elif type(curr) is Jump and curr.dir == ARROW_UP:
            print ">> jump. ", stack
            cond = condition
            if stack[-1].node.type == "in":
                cond = cond + stack[-1].node.signals
                # print ".. cond ", cond
                stack.pop()

                # print "==> ", start + 1, self.jump_down[curr.index]
                self._make(start + 1, stack[:], cond)
                assert_b(curr.index in self.jump_down, "no [%d] down arrow" % curr.index)
                self._make(self.jump_down[curr.index], stack[:], self._invert(cond))
            else:
                # print "==> ", self.jump_down[curr.index]
                assert_b(curr.index in self.jump_down, "no [%d] down arrow" % curr.index)
                self._make(self.jump_down[curr.index], stack[:], cond)
            # if type(stack[-1])
        elif type(curr) is Jump and curr.dir == ARROW_DOWN:
            # pass it by
            # print "pass"
            self._make(start + 1, stack[:], condition)
        else:
            print "wtf: ", curr



    def analysis(self):
        self.enumerated = []
        nodeid = 0
        self.barenodes = {}
        for nid,s in enumerate(self.parsed):
            if type(s) is not Jump:
                if type(s) == Control or (type(s) == Node and s.type == 'out'):
                    nodeid += 1
                    cnode = CertainNode(id=nid+1, nodeid=nodeid, node=s)
                    self.barenodes[nodeid] = cnode
                    self.enumerated.append(cnode)
                else:
                    self.enumerated.append(CertainNode(id=nid+1, nodeid=0, node=s))
            else:
                self.enumerated.append(s)

        self.out_signals = list(chain(*[e.signals for e in self.parsed if type(e) is Node and e.type=='out']))
        self.in_signals = list(chain(*[e.signals for e in self.parsed if type(e) is Node and e.type=='in']))
        self.arrow_up = [e for e in self.parsed if type(e) is Jump and e.dir==ARROW_UP]
        self.arrow_down = [e for e in self.parsed if type(e) is Jump and e.dir==ARROW_DOWN]
        self.signal_sanity_check(self.out_signals)
        self.signal_sanity_check(self.in_signals)
        self.arrow_sanity_check(self.arrow_up)
        self.arrow_sanity_check(self.arrow_down)
        arrow_down_indexes = {x.index for x in self.arrow_down}
        assert_b(len(arrow_down_indexes) == len(self.arrow_down), "Several DOWN arrows not allowed!")


        stack = []
        for s in self.parsed:
            if type(s) is Control and not len(stack):
                stack.append(s)
            elif type(s) is CertainNode and s.node.type == 'out':
                stack.append(s)

        self.jump_up = []
        self.jump_down = {}
        for i,s in enumerate(self.parsed):
            if type(s) == Jump and s.dir == ARROW_UP:
                self.jump_up.append((s.index, i))
            if type(s) == Jump and s.dir == ARROW_DOWN:
                self.jump_down[s.index] = i

        self._make(0, [], [])


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = LSAAnalyser(parse(s))
    p.analysis()
    print p.connections