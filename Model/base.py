from itertools import combinations, chain, permutations, combinations_with_replacement
import re
from model import TwoModel, ThreeModel, FiveModel
from prettytable import PrettyTable


class CycleFoundException(Exception):
    pass


def format_test(test):
    r = ""
    for k in sorted(test.keys()):
        r += "%s:%s, " % (k, test[k])
    return r


class BaseModel(object):
    DEFAULT = None

    def __init__(self, data):
        self.problems = []
        self.actions = self.fill_actions()
        self.data = data
        self.functions = self.data['functions']
        variables = {v: self.DEFAULT for v in list(self.functions.keys())}
        variables.update(self.data['inputs'][0])
        self.test = self.data['inputs'][0]
        self.variables = variables
        self.columns = sorted(variables)
        self.table = PrettyTable(['#'] + self.columns)
        if 'result_func' in self.data:
            self.result_func = self.data['result_func']
        else:
            self.result_func = None

    def find_races(self):
        input_vars = sorted(self.data['inputs'][0].copy())
        vals = sorted(chain(*[set(permutations(x)) for x in combinations_with_replacement([0, 1], len(input_vars))]))
        for testv in vals:
            test = {var: str(val) for var, val in zip(input_vars, testv)}
            print()
            print("TESTING %s" % format_test(test))
            for test in self._prepare_test(test):
                self.test = test
                self.variables.update(test)
                self._run(output=True)
                self._analyze()
                self._cleanup()

        print()
        print("=========================================")
        print("Found issues:")
        tbl = PrettyTable(["Title", "Data"])
        for pr in self.problems:
            tbl.add_row(pr)
        print(tbl)

    def _prepare_test(self, test):
        return [test]

    def _analyze(self):
        pass

    def do_model(self):
        for test in self.data['inputs']:
            self.variables.update(self.data['inputs'][0])
            print("TESTING %s" % format_test(test))
            for test in self._prepare_test(test):
                self.test = test
                self.variables.update(test)
                self._run(output=True)
                self._analyze()
                self._cleanup()

        print()
        print("=========================================")
        print("Found issues:")
        tbl = PrettyTable(["Title", "Data"])
        for pr in self.problems:
            tbl.add_row(pr)
        print(tbl)

    def _run(self, output=True):
        self.add_row()
        try:
            self.start_model()
        except CycleFoundException as e:
            if output:
                print(self.table)
                msg = "Circuit is not stable", format_test(self.test)
                print(msg)
                if msg not in self.problems:
                    self.problems.append(msg)
        else:
            if output:
                print(self.table)

    def _cleanup(self):
        self.table = PrettyTable(['#'] + self.columns)


class IterativeModel(BaseModel):
    def __init__(self, data):
        self.history = []
        super(IterativeModel, self).__init__(data)

    def do_iteration(self):
        new_vars = self.variables.copy()
        locals = self.variables.copy()
        locals.update(self.actions)
        for var, func in self.functions.items():
            r = eval(func, locals)
            new_vars[var] = r
        if self.variables == new_vars:
            self.add_row()
            return True
        self.variables = new_vars
        self.add_row()
        return False

    def start_model(self):
        while not self.do_iteration():
            pass

    def add_row(self):
        row = [len(self.table._rows) + 1]
        for c in self.columns:
            row.append(self.variables[c])
        if row[1:] in self.history and self.history[-1] != row[1:]:
            row[0] = "!%d!" % (self.history.index(row[1:]) + 1)
            self.table.add_row(row)
            raise CycleFoundException(row)
        self.history.append(row[1:])
        self.table.add_row(row)

    def _cleanup(self):
        super()._cleanup()
        self.history = []

    def _analyze(self):
        signals = zip(*self.history)
        for i, var_h in enumerate(signals):
            v_str = ''.join(var_h)
            ones = len(re.findall('1+', v_str))
            zeros = len(re.findall('0+', v_str))
            var = self.columns[i]
            if ones + zeros > 2:
                msg = "Race condition", "{} [{}]".format(var, format_test(self.test))
                if msg not in self.problems:
                    self.problems.append(msg)
                print(msg)

            if self.result_func:
                locals = self.variables.copy()
                locals.update(self.actions)
                is_conform = eval(self.result_func, locals)
                if not is_conform:
                    msg = "Circuit doesn't corresponds equation", format_test(self.test)
                    if msg not in self.problems:
                        self.problems.append(msg)
                    print(msg)


class Iterative2Model(TwoModel, IterativeModel):
    pass


class Iterative3Model(ThreeModel, IterativeModel):
    def _prepare_test(self, test):
        r = {}
        for var, x in test.items():
            if self.test[var] != x:
                r[var] = 'x'
            else:
                r[var] = x
        if 'x' in r.values():
            return [r, test]
        else:
            return [r]

    def _analyze(self):
        super()._analyze()
        if 'x' in self.history[-1] and 'x' not in self.test.values():
            msg = ("Bad circuit. Can't model", format_test(self.test))
            if msg not in self.problems:
                self.problems.append(msg)


class Iterative5Model(FiveModel, IterativeModel):
    def _prepare_test(self, test):
        r = {}
        for var, x in test.items():
            if self.test[var] != x:
                if self.test[var] == '1' and x == '0':
                    r[var] = 'p'
                else:
                    r[var] = 'h'
            else:
                r[var] = x
        if 'p' in r.values() or 'h' in r.values():
            return [r, test]
        else:
            return [r]
