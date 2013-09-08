from consts import *
from parse import parse
from itertools import chain

class LSAAlgorithmError(Exception):
    pass

def assert_b(boolean, message="assertion failed"):
    if not boolean:
        raise LSAAlgorithmError(message)

End = namedtuple('End', ['node'])
Intermediate = namedtuple('Intermediate', ['node', 'fr', 'to'])

class GraphNode(object):
    def __init__(self, node):
        self.node = node

    def __repr__(self):
        return "obj-" + str(self.node)


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


    def _invert(self, signals):
        return [Signal(name=x.name, index=x.index, inverted=not x.inverted) for x in signals]

    def _make(self, start, stack, condition):
        if start >= len(self.enumerated): return
        if start == 0:
            self.connections = []

        print "* ", start, stack

        curr = self.enumerated[start]
        if type(curr) is CertainNode:
            print ">> node. ", curr
            if len(stack):
                assert_b(type(stack[-1].node) is Control or stack[-1].node.type == 'out',
                    'expected jump after input node')
                if type(curr.node) is Control or curr.node.type == 'out':
                    print r"%%", (stack[-1], curr), condition
                    self.connections.append((stack[-1].nodeid, curr.nodeid, condition))
                    stack.pop()
            self._make(start + 1, stack + [curr], [])

        elif type(curr) is Jump and curr.dir == ARROW_UP:
            print ">> jump. ", stack
            cond = condition
            if stack[-1].node.type == "in":
                cond = cond + stack[-1].node.signals
                print ".. cond ", cond
                stack.pop()

                print "==> ", start + 1, self.jump_down[curr.index]
                self._make(start + 1, stack[:], cond)
                self._make(self.jump_down[curr.index], stack[:], self._invert(cond))
            else:
                print "==> ", self.jump_down[curr.index]
                self._make(self.jump_down[curr.index], stack[:], cond)
            # if type(stack[-1])
        elif type(curr) is Jump and curr.dir == ARROW_DOWN:
            # pass it by
            print "pass"
            self._make(start + 1, stack[:], condition)
        else:
            print "wtf: ", curr



    def analysis(self):
        # machine = self.lca_machine()
        # machine.next()
        print self.parsed
        # self.nodes = [GraphNode(x) for x in self.parsed]
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

        print self.enumerated
        print self.barenodes

        out_signals = list(chain(*[e.signals for e in self.parsed if type(e) is Node and e.type=='out']))
        in_signals = list(chain(*[e.signals for e in self.parsed if type(e) is Node and e.type=='in']))
        self.signal_sanity_check(out_signals)
        self.signal_sanity_check(in_signals)

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

        print self.jump_up
        print self.jump_down
        print "============"
        print self._make(0, [], [])
        print "============"
        print self.connections


if __name__ == '__main__':
    s = u'\u25cbX\u2081\u2191\u2081(Y\u2081Y\u2082)\u2191\u2082\u2193\u2081Y\u2082\u2193\u2082\u25cf'
    print s
    p = LSAAnalyser(parse(s))
    print p.analysis()
