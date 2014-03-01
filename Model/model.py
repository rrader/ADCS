class TwoModel(object):
    DEFAULT = '0'

    def fill_actions(self):
        q = lambda x: bool(int(x))
        return {'_and': lambda a, b: '1' if q(a) and q(b) else '0',
                '_or': lambda a, b: '1' if q(a) or q(b) else '0',
                '_not': lambda a: '1' if not q(a) else '0',
                }


class ThreeModel(object):
    DEFAULT = 'x'

    def fill_actions(self):
        def _and(a, b):
            t = {('0', '0'): '0',
                 ('0', '1'): '0',
                 ('0', 'x'): '0',
                 ('1', '0'): '0',
                 ('1', '1'): '1',
                 ('1', 'x'): 'x',
                 ('x', '0'): '0',
                 ('x', '1'): 'x',
                 ('x', 'x'): 'x',
                 }
            return t[a, b]

        def _or(a, b):
            t = {('0', '0'): '0',
                 ('0', '1'): '1',
                 ('0', 'x'): 'x',
                 ('1', '0'): '1',
                 ('1', '1'): '1',
                 ('1', 'x'): '1',
                 ('x', '0'): 'x',
                 ('x', '1'): '1',
                 ('x', 'x'): 'x',
                 }
            return t[a, b]

        def _not(a):
            t = {'0': '1',
                 '1': '0',
                 'x': 'x'
                 }
            return t[a]

        return {'_and': _and,
                '_or': _or,
                '_not': _not,
                }


class FiveModel(object):
    DEFAULT = 'x'

    def fill_actions(self):
        def _and(a, b):
            t = {('0', '0'): '0',
                 ('0', '1'): '0',
                 ('0', 'x'): '0',
                 ('0', 'p'): '0',
                 ('0', 'h'): '0',

                 ('1', '0'): '0',
                 ('1', '1'): '1',
                 ('1', 'x'): 'x',
                 ('1', 'p'): 'p',
                 ('1', 'h'): 'h',

                 ('x', '0'): '0',
                 ('x', '1'): 'x',
                 ('x', 'x'): 'x',
                 ('x', 'p'): 'x',
                 ('x', 'h'): 'x',

                 ('p', '0'): '0',
                 ('p', '1'): 'p',
                 ('p', 'x'): 'x',
                 ('p', 'p'): 'p',
                 ('p', 'h'): 'x',

                 ('h', '0'): '0',
                 ('h', '1'): 'h',
                 ('h', 'x'): 'x',
                 ('h', 'p'): 'x',
                 ('h', 'h'): 'h',
                 }
            return t[a, b]

        def _or(a, b):
            t = {('0', '0'): '0',
                 ('0', '1'): '1',
                 ('0', 'x'): 'x',
                 ('0', 'p'): 'p',
                 ('0', 'h'): 'h',

                 ('1', '0'): '1',
                 ('1', '1'): '1',
                 ('1', 'x'): '1',
                 ('1', 'p'): '1',
                 ('1', 'h'): '1',

                 ('x', '0'): 'x',
                 ('x', '1'): '1',
                 ('x', 'x'): 'x',
                 ('x', 'p'): 'x',
                 ('x', 'h'): 'h',

                 ('p', '0'): 'p',
                 ('p', '1'): '1',
                 ('p', 'x'): 'x',
                 ('p', 'p'): 'p',
                 ('p', 'h'): 'x',

                 ('h', '0'): '0',
                 ('h', '1'): '1',
                 ('h', 'x'): 'h',
                 ('h', 'p'): 'x',
                 ('h', 'h'): 'h',
                 }
            return t[a, b]

        def _not(a):
            t = {'0': '1',
                 '1': '0',
                 'x': 'x',
                 'p': 'h',
                 'h': 'p'
                 }
            return t[a]

        return {'_and': _and,
                '_or': _or,
                '_not': _not,
                }