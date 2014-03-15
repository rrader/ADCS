#http://sebsauvage.net/python/gui/
from collections import OrderedDict
from copy import deepcopy
from itertools import groupby, tee
import json
from math import ceil, floor
from operator import itemgetter
from optparse import OptionParser

from tkinter import *
from tkinter import simpledialog


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def fill_zone(i, j, z, patterns, contains, value):
    if i < 0 or j < 0 or z < 0: return
    try:
        if patterns[z][j][i] == contains:
            patterns[z][j][i] = value
            fill_zone(i + 1, j, z, patterns, contains, value)
            fill_zone(i - 1, j, z, patterns, contains, value)
            fill_zone(i, j + 1, z, patterns, contains, value)
            fill_zone(i, j - 1, z, patterns, contains, value)
            fill_zone(i, j, z + 1, patterns, contains, value)
            fill_zone(i, j, z - 1, patterns, contains, value)
    except IndexError:
        pass


class Editor(Tk):
    def __init__(self, parent=None, board=None, components=None):
        if not board:
            board = {}
        super().__init__(parent)
        self.ic = board
        self.components = components
        self.parent = parent
        self.layer = 1
        self.is_draw_pattern = False
        self.is_draw_routes = False
        self.build()
        self.build_patterns()
        self.do_routing()
        self.draw_all()
        # self.pattern = self.build_pattern()

    def enumerate_lines(self):
        lines = {}
        index = 0
        for c in self.ic.components:
            cls = AttrDict(self.components[c["type"]])
            if "connect" in c:
                for i, conn_to in enumerate(c["connect"]):
                    conn_from = "{}:{}".format(c["name"], i)
                    new_ind = lines.get(conn_from)
                    if new_ind is None and conn_to is not None:
                        new_ind = lines.get(conn_to)
                    if new_ind is None:
                        index += 1
                        new_ind = index

                    if conn_to is not None:
                        lines[conn_to] = new_ind
                    lines[conn_from] = new_ind
            else:
                for i, position in enumerate(cls["contacts"]):
                    conn_from = "{}:{}".format(c["name"], i)
                    new_ind = lines.get(conn_from)
                    if new_ind is None:
                        index += 1
                        new_ind = index
                    lines[conn_from] = new_ind
        print(lines)
        return lines

    def do_routing(self):
        lines = OrderedDict(self.enumerate_lines())

        # self.patterns, pathes = self.route_for_pins(1)
        pathes_d = {}
        sorted_lines = sorted(lines.items(), key=itemgetter(1))
        for key, group in groupby(sorted_lines, key=itemgetter(1)):
            self.patterns, pathes = self.route_for_pins(key)
            pathes_d[key] = pathes
            # print(pathes)
        # self.patterns, pathes = self.route_for_pins(1, max_steps=40)
        # print(self.patterns)
        self.pathes = pathes_d

    def count_zones(self, value, patterns):
        patterns = deepcopy(patterns)
        found = True
        count = 0

        def fill_zone(i, j, z):
            if i < 0 or j < 0 or z < 0: return
            try:
                if patterns[z][j][i] == value:
                    patterns[z][j][i] = 0
                    fill_zone(i + 1, j, z)
                    fill_zone(i - 1, j, z)
                    fill_zone(i, j + 1, z)
                    fill_zone(i, j - 1, z)
                    fill_zone(i, j, z + 1)
                    fill_zone(i, j, z - 1)
            except IndexError:
                pass

        while found:
            found = False
            for z, pattern in enumerate(patterns):
                for j, line in enumerate(pattern):
                    for i, cell in enumerate(line):
                        if cell == value:
                            fill_zone(i, j, z)
                            count += 1
                            found = True
                            break
        return count


    def prepare_zones(self, value, patterns):
        self._prepare_zones(value, patterns)
        found = True
        index = -2

        while found:
            found = False
            for z, pattern in enumerate(patterns):
                for j, line in enumerate(pattern):
                    for i, cell in enumerate(line):
                        if cell == 1:
                            fill_zone(i, j, z, patterns, 1, index)
                            # index += 1
                            found = True
                            return

    def _prepare_zones(self, value, patterns):
        for z, pattern in enumerate(patterns):
            for j, line in enumerate(pattern):
                for i, cell in enumerate(line):
                    if cell == value:
                        patterns[z][j][i] = 1
                    elif cell != value and cell != 0:
                        if cell > 0:
                            patterns[z][j][i] = -1
                            self.surround_with_block(i, j, z, patterns)
                        else:
                            patterns[z][j][i] = -1

    def set_block(self, i, j, z, pattern):
        try:
            if pattern[z][j][i] == 0:
                pattern[z][j][i] = -1
        except IndexError:
            pass

    def surround_with_block(self, i, j, z, pattern):
        if i < 0 or j < 0 or z < 0: return
        self.set_block(i + 1, j, z, pattern)
        self.set_block(i - 1, j, z, pattern)
        self.set_block(i, j + 1, z, pattern)
        self.set_block(i, j - 1, z, pattern)
        # self.set_block(i, j, z + 1, pattern)
        # self.set_block(i, j, z - 1, pattern)

    def route_for_pins(self, key, fake=False, max_steps=None, max_paths=None):
        def try_set(i, j, z, value):
            if i < 0 or j < 0 or z < 0: return 0
            try:
                if step_num[z][j][i] == -2:
                    raise StopIteration((i, j, z))
                elif step_num[z][j][i] == 0 or \
                                step_num[z][j][i] > value:
                    step_num[z][j][i] = value
                    return 1
                    # patterns[z][j][i] = key
            except IndexError:
                pass
            return 0

        def can_make_hole(i, j):
            ret = True
            for z in range(self.ic.layers):
                ret = ret and origin_patterns[z][j][i] == 0
            return ret

        def do_wave():
            c = 0
            for z, pattern in enumerate(step_num):
                for j, line in enumerate(pattern):
                    for i, cell in enumerate(line):
                        if step_num[z][j][i] == step:
                            try:
                                c += try_set(i + 1, j, z, step + 1)
                                c += try_set(i - 1, j, z, step + 1)
                                c += try_set(i, j + 1, z, step + 1)
                                c += try_set(i, j - 1, z, step + 1)
                                if can_make_hole(i, j):
                                    c += try_set(i, j, z + 1, step + 1)
                                    c += try_set(i, j, z - 1, step + 1)
                            except StopIteration as e:
                                return e.value
            if c == 0:
                raise StopIteration("no way")

        def do_backtrace(ti, tj, tz, step):
            path = []
            i, j, z = ti, tj, tz
            step += 1
            while step_num[z][j][i] != 1:
                path.append((i, j, z))
                step -= 1
                try:
                    if step_num[z][j][i + 1] == step - 1:
                        i, j, z = i + 1, j, z
                        continue
                except IndexError:
                    pass
                try:
                    if step_num[z][j][i - 1] == step - 1:
                        i, j, z = i - 1, j, z
                        continue
                except IndexError:
                    pass
                try:
                    if step_num[z][j + 1][i] == step - 1:
                        i, j, z = i, j + 1, z
                        continue
                except IndexError:
                    pass
                try:
                    if step_num[z][j - 1][i] == step - 1:
                        i, j, z = i, j - 1, z
                        continue
                except IndexError:
                    pass
                try:
                    if step_num[z + 1][j][i] == step - 1:
                        i, j, z = i, j, z + 1
                        continue
                except IndexError:
                    pass
                try:
                    if step_num[z - 1][j][i] == step - 1 and z-1 >= 0:
                        i, j, z = i, j, z - 1
                        continue
                except IndexError:
                    pass
            path.append((i, j, z))
            print(path)
            return path

        origin_patterns = self.patterns
        step_num = deepcopy(origin_patterns)
        self.prepare_zones(key, step_num)

        pathes = []

        while self.count_zones(1, step_num) > 0:
            step = 1
            while True:
                # wave
                try:
                    ret = do_wave()
                    if ret is not None:
                        ti, tj, tz = ret
                        path = do_backtrace(ti, tj, tz, step + 1)
                        print(">>",path)
                        break
                    step += 1
                    if max_steps is not None and step > max_steps:
                        return step_num, []
                except StopIteration:
                    print("ERROR")
                    return step_num, []

            pathes.append(path)
            for i, j, z in path:
                origin_patterns[z][j][i] = key

            step_num = deepcopy(origin_patterns)
            self.prepare_zones(key, step_num)

        for path in pathes:
            for i, j, z in path:
                self.surround_with_block(i, j, z, origin_patterns)
        return origin_patterns, pathes
        # if not fake:
        #     return origin_patterns
        # else:
        #     return step_num

    def build_patterns(self):
        patterns = []
        for i in range(1, self.ic.layers + 1):
            patterns.append(self.build_pattern(layer=i))
        self.patterns = patterns

    def fill_rectangle(self, pattern, x1, y1, x2, y2, fill=-1):
        for x in range(int(floor(x1 / self.ic.grid)), int(ceil(x2 / self.ic.grid))):
            for y in range(int(floor(y1 / self.ic.grid)), int(ceil(y2 / self.ic.grid))):
                pattern[y][x] = fill

    def change_layer(self):
        layer = simpledialog.askinteger("Layer", "Layer")
        if not layer:
            return
        self.layer = layer
        self.redraw()

    def redraw(self):
        self.canvas.delete(ALL)
        # self.pattern = self.build_pattern()
        self.pattern = self.patterns[self.layer - 1]
        if self.is_draw_pattern:
            self.draw_pattern()
        else:
            self.draw_all()

    def toggle_pattern(self):
        self.is_draw_pattern = not self.is_draw_pattern
        self.redraw()

    def toggle_routes(self):
        self.is_draw_routes = not self.is_draw_routes
        self.redraw()

    def build(self):
        top = Frame(self)
        bottom = Frame(self)
        top.pack(side=TOP)
        bottom.pack(side=BOTTOM, fill=BOTH, expand=True)

        b = Button(self, text="Layer", width=4, height=1, command=self.change_layer)
        p = Button(self, text="Pattern", width=4, height=1, command=self.toggle_pattern)
        r = Button(self, text="Routes", width=4, height=1, command=self.toggle_routes)
        b.pack(in_=top, side=LEFT)
        p.pack(in_=top, side=LEFT)
        r.pack(in_=top, side=LEFT)

        self.canvas = Canvas(self, width=950, height=600, bg='white')
        self.canvas.pack(in_=bottom)

    def draw_all(self):
        self.draw_grid()
        self.draw_components()
        self.draw_routes()

    def draw_routes(self):
        if not self.is_draw_routes: return
        for key, pathes in self.pathes.items():
            for path in pathes:
                for (i,j,z), (i2,j2,z2) in pairwise(path):
                    if z != z2:
                        print(">> ", (i,j,z), (i2,j2,z2))
                        self.canvas.create_oval(self.c((i+0.5-0.4) * self.ic.grid),
                                                self.c((j+0.5-0.4) * self.ic.grid),
                                                self.c((i+0.5+0.4) * self.ic.grid),
                                                self.c((j+0.5+0.4) * self.ic.grid),
                                                fill="black", tags=("hole",))
                    elif z + 1 == self.layer:
                        self.canvas.create_line(self.c((i+0.5) * self.ic.grid),
                                                self.c((j+0.5) * self.ic.grid),
                                                self.c((i2+0.5) * self.ic.grid),
                                                self.c((j2+0.5) * self.ic.grid),
                                                width=3,
                                                fill="green")
        self.canvas.tag_raise("hole")

    def draw_pattern(self):
        self.draw_grid()
        print(self.pattern)
        for j, line in enumerate(self.pattern):
            for i, cell in enumerate(line):
                if self.pattern[j][i] == -1:
                    c = "gray"
                elif self.pattern[j][i] == -2:
                    c = "green"
                elif self.pattern[j][i] > 0:
                    c = "yellow"
                else:
                    c = "white"
                self.canvas.create_rectangle(self.c(i * self.ic.grid),
                                             self.c(j * self.ic.grid),
                                             self.c((i + 1) * self.ic.grid),
                                             self.c((j + 1) * self.ic.grid),
                                             fill=c, outline="gray",
                                             dash=(2, 2))
                if self.pattern[j][i] != 0:
                    i = self.canvas.create_text(self.c((i + 0.5) * self.ic.grid),
                                                self.c((j + 0.5) * self.ic.grid),
                                                text=self.pattern[j][i],
                                                font=("Monospace", 4))

    def build_pattern(self, layer=None):
        if layer is None:
            layer = self.layer
        lines = self.enumerate_lines()
        line = lambda: [0 for _ in range(int(self.ic.size[0] / self.ic.grid))]
        pattern = [line() for _ in range(int(self.ic.size[1] / self.ic.grid))]
        for c in self.ic.components:
            cls = AttrDict(self.components[c["type"]])
            if layer == 1 or ("through" in cls and cls["through"]):
                self.fill_rectangle(pattern,
                                    c["position"][0],
                                    c["position"][1],
                                    c["position"][0] + cls.size[0],
                                    c["position"][1] + cls.size[1])
                for i, (ct_x, ct_y) in enumerate(cls["contacts"]):
                    cs = cls["contact_pad"]
                    connector_name = "{}:{}".format(c["name"], i)
                    self.fill_rectangle(pattern,
                                        c["position"][0] + ct_x - cs[0] / 2,
                                        c["position"][1] + ct_y - cs[1] / 2,
                                        c["position"][0] + ct_x + cs[0] / 2,
                                        c["position"][1] + ct_y + cs[1] / 2,
                                        fill=lines[connector_name])
        return pattern

    def draw_components(self):
        for c in self.ic.components:
            cls = AttrDict(self.components[c["type"]])
            if self.layer == 1 or ("through" in cls and cls["through"]):
                self.canvas.create_rectangle(self.c(c["position"][0]), self.c(c["position"][1]),
                                             self.c(c["position"][0] + cls.size[0]),
                                             self.c(c["position"][1] + cls.size[1]),
                                             fill="gray",
                                             width=1, tags=("component",))
                for i, (ct_x, ct_y) in enumerate(cls["contacts"]):
                    cs = cls["contact_pad"]
                    if "through" in cls and cls["through"]:
                        self.canvas.create_oval(self.c(c["position"][0] + ct_x - cs[0] / 2),
                                                self.c(c["position"][1] + ct_y - cs[1] / 2),
                                                self.c(c["position"][0] + ct_x + cs[0] / 2),
                                                self.c(c["position"][1] + ct_y + cs[1] / 2),
                                                width=1, tags=("component", c["type"],
                                                               c["name"]),
                                                fill="black")
                    else:
                        self.canvas.create_rectangle(self.c(c["position"][0] + ct_x - cs[0] / 2),
                                                     self.c(c["position"][1] + ct_y - cs[1] / 2),
                                                     self.c(c["position"][0] + ct_x + cs[0] / 2),
                                                     self.c(c["position"][1] + ct_y + cs[1] / 2),
                                                     width=1, tags=("component", c["type"],
                                                                    c["name"]),
                                                     fill="gold")
                    name = c["connect"][i] if "connect" in c and c["connect"][i] is not None else "-"
                    self.canvas.create_text(self.c(c["position"][0] + ct_x - cs[0] / 2),
                                            self.c(c["position"][1] + ct_y + cs[1] / 2),
                                            justify="center",
                                            font=("Helvetica", 8),
                                            fill="blue",
                                            text="%d: %s" % (i, name),
                                            tags=(c["name"] + "text"))
                if "text_margin" in cls:
                    text_margin = cls["text_margin"]
                else:
                    text_margin = [0, 0]
                self.canvas.create_text(self.c(c["position"][0] + cls.size[0] / 2 + text_margin[0]),
                                        self.c(c["position"][1] + cls.size[1] / 2 + text_margin[1]),
                                        text=c["name"],
                                        justify="center",
                                        fill="black")

    def c(self, size):
        """convert mm to pixels
        """
        return size * self.ic.resolution

    def draw_grid(self):
        self.canvas.config(background="gray")
        self.canvas.create_rectangle(0, 0, self.c(self.ic.size[0]), self.c(self.ic.size[1]), fill="lightgreen")
        for i in range(int(self.ic.size[1] / self.ic.grid)):
            if (i * self.ic.grid) % 5 == 0:
                w = 2
                c = "gray"
            else:
                w = 1
                c = "white"
            self.canvas.create_line(0, self.c(i * self.ic.grid), self.c(self.ic.size[0]), self.c(i * self.ic.grid),
                                    fill=c, width=w, dash=(2, 2))
        for i in range(int(self.ic.size[0] / self.ic.grid)):
            if (i * self.ic.grid) % 5 == 0:
                w = 1
                c = "gray"
            else:
                w = 1
                c = "white"
            self.canvas.create_line(self.c(i * self.ic.grid), 0, self.c(i * self.ic.grid), self.c(self.ic.size[1]),
                                    fill=c, width=w, dash=(2, 2))

    def xc(self, size):
        """convert pixels to mm
        """
        return size / self.ic.resolution


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="open FILE", metavar="FILE")

    (options, args) = parser.parse_args()
    if not options.filename:
        options.filename = 'default.json'
    data = json.loads(open(options.filename).read())
    ui = Editor(None, AttrDict(data["board"]), AttrDict(data["components"]))
    ui.title('Editor')
    ui.mainloop()
