import string
import pickle
import os
import warnings

from PyQt4 import uic
from PyQt4 import QtCore, QtGui
import yaml

import vhdl
import analysis
import parse
import graph
import machine
import mtable
from consts import *

path = os.path.dirname(__file__)

(Ui_ADCSWindow, QMainWindow) = uic.loadUiType(os.path.join(path, 'adcswindow.ui'))

IMG_PATH = os.getcwd() + "/graph.png"
IMG_MACHINE_PATH = os.getcwd() + "/machine.png"
IMG_FORMULAS_PATH = os.getcwd() + "/adcs_1.png"

def upper_index(num):
    symbol_index = SUPERSCRIPT[num]
    return unichr(symbol_index)


def lower_index(num):
    symbol_index = SUBSCRIPT[num]
    return unichr(symbol_index)


class MatrixModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, analyser):
        QtCore.QAbstractTableModel.__init__(self)
        self.gui = parent
        self.analyser = analyser
        self.node_names = sorted([nodename(k, {k: x}) for k,x in self.analyser.barenodes.iteritems()])
        self.node_count = len(self.node_names)
        self.colLabels = self.node_names

    def rowCount(self, parent):
        return len(self.node_names)

    def columnCount(self, parent):
        return len(self.node_names)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return QtCore.QVariant()
        value = ''
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            cond = self.analyser.matrix[row][col]
            value = conditionname_b(cond)
        return QtCore.QVariant(value)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.colLabels[section])
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.colLabels[section])
        return QtCore.QVariant()

def is_comform(item, q, signals):
    ok = True
    lst = [mtable.condition(name='q', index=i, val=int(v)) for i,v in enumerate(q)] + \
          [mtable.condition(name='X', index=k, val=int(v)) for k,v in signals.iteritems()]
    for q in lst:
        ok = ok and any([it == q for it in item])
    return ok


class TransitionModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, mtable, model, jk):
        QtCore.QAbstractTableModel.__init__(self)
        self.gui = parent
        self.mtable = mtable
        self.model = model
        self.jk = jk
        self.data = []
        for t in self.mtable:
            ln = list(t.q) + list(t.q2)
            signals = {sx.index: not sx.inverted for sx in t.signals}
            for s in self.model.in_signals:
                if s.index in signals:
                    ln.append(str(1 if signals[s.index] else 0))
                else:
                    ln.append("-")
            ys = {sx.index: not sx.inverted for sx in t.y}
            for s in sorted(self.model.out_signals, key=lambda x:x.index):
                if s.index in ys:
                    ln.append(str(1 if ys[s.index] else 0))
                else:
                    ln.append(str(0))
            for char in jk:
                for item in char:
                    ln.append('1' if any([is_comform(simple, t.q, signals) for simple in item]) else '0')
                        
            self.data.append(ln)

        self.headers = ["Q%s" % i for i in range(len(self.mtable[0].q))] + \
              ["Q%s+1" % i for i in range(len(self.mtable[0].q))] + \
              ["X%d" % s.index for s in self.model.in_signals] + \
              ["Y%d" % s.index for s in sorted(self.model.out_signals, key=lambda x:x.index)] + \
              ["J%d" % (i+1) for i in range(len(self.mtable[0].q))] + \
              ["K%d" % (i+1) for i in range(len(self.mtable[0].q))] + \
              ["Y%d" % (i+1) for i in range(len(self.mtable[0].q))]

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.data[0])

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return QtCore.QVariant()
        value = ''
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            col = index.column()
            value = self.data[row][col]
        return QtCore.QVariant(value)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.headers[section])
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(str(section+1))
        return QtCore.QVariant()


class ADCSWindow (QMainWindow):
    """ADCSWindow inherits QMainWindow"""
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ADCSWindow()
        self.ui.setupUi(self)

        pic = QtGui.QLabel(self)
        # pic.setGeometry(10, 10, 400, 100)
        self.canvas = pic
        pic.setScaledContents(True)
        pic.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)

        scrollArea = QtGui.QScrollArea(self)
        scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        scrollArea.setWidget(pic)

        self.ui.innerLayout.addWidget(scrollArea)
        self.ui.innerLayout.setStretch(0,2)
        self.ui.innerLayout.setStretch(1,1)



        mpic = QtGui.QLabel(self)
        # pic.setGeometry(10, 10, 400, 100)
        self.m_canvas = mpic
        mpic.setScaledContents(True)
        mpic.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)

        scrollArea = QtGui.QScrollArea(self)
        scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        scrollArea.setWidget(mpic)

        self.ui.machineLayout.addWidget(scrollArea)
        self.ui.machineLayout.setStretch(0,2)
        self.ui.machineLayout.setStretch(1,1)
        self.ui.machineLayout.setStretch(2,4)


        fpic = QtGui.QLabel(self)
        # pic.setGeometry(10, 10, 400, 100)
        self.f_canvas = fpic
        fpic.setScaledContents(True)
        fpic.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)

        scrollArea = QtGui.QScrollArea(self)
        scrollArea.setBackgroundRole(QtGui.QPalette.Light)
        scrollArea.setWidget(fpic)
        self.ui.formulasLayout.addWidget(scrollArea)

        # self.connect(self.ui.toolButton_Start,
        #              QtCore.SIGNAL('clicked()'), QtCore.SLOT('test_unicode()'))
        self.ui.actionNew.triggered.connect(self.newDocument)
        self.ui.actionExit.triggered.connect(self.exitApp)
        self.ui.actionAnalyse.triggered.connect(self.validate)
        self.ui.actionSave_alg.triggered.connect(self.save_alg)
        self.ui.actionSave_bin.triggered.connect(self.save_bin)
        self.ui.actionOpen_alg.triggered.connect(self.open_alg)
        self.ui.actionOpen_bin.triggered.connect(self.open_bin)
        self.ui.actionSave_machine.triggered.connect(self.save_machine)
        self.ui.actionOpen_machine.triggered.connect(self.open_machine)
        self.ui.actionSave_vhdl.triggered.connect(self.save_vhdl)
        self.ui.textEdit.installEventFilter(self)

        self.clear()

    def clear(self):
        self.no_alg = False
        if os.path.exists(IMG_PATH):
            os.remove(IMG_PATH)
        if os.path.exists(IMG_MACHINE_PATH):
            os.remove(IMG_MACHINE_PATH)
        if os.path.exists(IMG_FORMULAS_PATH):
            os.remove(IMG_FORMULAS_PATH)
        self.ui.textEdit.setPlainText(u'\u25cb\u25cf')
        self.model = None
        self.machine = None
        self.tr_table = None
        self._updateMode()


    def __del__(self):
        self.ui = None

    def newDocument(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            "You will lose unsaved work", QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.clear()
            self.ui.textEdit.setPlainText(u'\u25cb\u25cf')
            self.canvas.clear()

    def exitApp(self):
        reply = QtGui.QMessageBox.question(self, 'Confirm',
            "You will lose unsaved work", QtGui.QMessageBox.Yes | 
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            QtGui.QApplication.quit()

    def _updateMode(self):
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.editorTab), not self.no_alg)
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.modelTab), bool(self.model))
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.analysisTab), bool(self.model))
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.machineTab), bool(self.machine))
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.tableTab), bool(self.tr_table))
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.vhdlTab), bool(self.machine))
        #use full ABSOLUTE path to the image, not relative
        ren = None
        self._update_graph()
        if self.machine:
            ren = graph.renumerate(self.machine[0])
            graph.draw_machine(*self.machine)
        self._fill_signals()
        if self.model:
            txt = self.ui.info.toPlainText()
            self.ui.info.setPlainText("%s\nInput signals: %d\nOutput signals: %d" % (txt, len(self.model.in_signals), len(self.model.out_signals)))
            graph.draw_graph(self.model.barenodes, self.model.connections, self.model.matrix, loop=self.model.loop, renumerated=ren)


        if os.path.exists(IMG_PATH):
            self.canvas.setPixmap(QtGui.QPixmap(IMG_PATH))
            self.canvas.adjustSize()

        if os.path.exists(IMG_MACHINE_PATH):
            self.m_canvas.setPixmap(QtGui.QPixmap(IMG_MACHINE_PATH))
            self.m_canvas.adjustSize()

        if os.path.exists(IMG_FORMULAS_PATH):
            self.f_canvas.setPixmap(QtGui.QPixmap(IMG_FORMULAS_PATH))
            self.f_canvas.adjustSize()


    def open_alg(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Algorithm', '', 
                "Algorithm .txt (*.txt)")
        if fname:
            self.clear()
            src = open(fname).read().decode('utf-8')
            self.ui.textEdit.setPlainText(src)
            self.log("file %s loaded (text)" % fname)
        self._updateMode()

    def open_bin(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Algorithm Model', '', 
                "Algorithm Model .alg (*.alg)")
        if fname:
            self.clear()
            self.model = pickle.load(open(fname))
            self.ui.textEdit.setPlainText(self.model.source)
            self._updateMode()
            self.log("file %s loaded (binary)" % fname)

    def save_alg(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Algorithm', '', 
                "Algorithm .txt (*.txt)")
        if fname:
            with open(fname, 'w') as f:
                src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
                f.write(src.encode('UTF-8'))

    def save_bin(self):
        if self.model:
            fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Algorithm Model', '', 
                    "Algorithm Model .alg (*.alg)")
            if fname:
                with open(fname, 'w') as f:
                    src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
                    self.model.source = src
                    pickle.dump(self.model, f)
        else:
            QtGui.QMessageBox.about(self, "Can't save", "Analyse your algorithm first")

    def save_machine(self):
        if self.machine:
            fname = QtGui.QFileDialog.getSaveFileName(self, 'Save Machine', '', 
                    "Machine .machine (*.machine)")
            if fname:
                with open(fname, 'w') as f:
                    src = yaml.dump(machine.to_dict(self.machine, self.tr_table), default_flow_style=False)
                    f.write(src)
        else:
            QtGui.QMessageBox.about(self, "Can't save", "Analyse your algorithm first")

    def save_vhdl(self):
        if self.model:
            fname = QtGui.QFileDialog.getSaveFileName(self, 'Save VHDL', '', 
                    "vhdl .vhd (*.vhd)")
            if fname:
                with open(fname, 'w') as f:
                    src = str(self.ui.vhdl_text.toPlainText().toUtf8()).decode('utf-8')
                    f.write(src.encode('UTF-8'))
        else:
            QtGui.QMessageBox.about(self, "Can't save", "Analyse your algorithm first")

    def open_machine(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Machine', '', 
                "Machine .machine (*.machine)")
        if fname:
            self.clear()
            src = open(fname).read().decode('utf-8')
            self.no_alg = True
            m = machine.from_dict(yaml.load(src))
            self.machine = m[:4]
            self.tr_table = m[4]
            self.log("file %s loaded (machine)" % fname)
        self._updateMode()

    def clear_log(self):
        self.ui.log.setPlainText(u"")

    def log(self, text, newline=True):
        if newline:
            text = text + "\n"
        self.ui.log.setPlainText(self.ui.log.toPlainText() + text)

    def _process(self, src):
        self.log("Parse... ", False)
        parsed = parse.parse(src)
        self.log("OK")
        self.log("Analyse... ", False)
        p = analysis.LSAAnalyser(parsed)
        p.analysis()
        self.log("OK")
        return p

    def _fill_signals(self):
        if self.model:
            self.ui.listSignals.clear()
            signals = sorted([conditionname([x]) for x in self.model.in_signals + self.model.out_signals])
            self.ui.listSignals.insertItems(0, QtCore.QStringList(signals))

            self.ui.listNodes.clear()
            nodes = sorted("%d: %d" % (k,x) for k,x in self.model.signals.iteritems())
            self.ui.listNodes.insertItems(0, QtCore.QStringList(nodes))

        machine = None
        if self.machine:
            machine = self.machine

        if machine:
            self.ui.listTransitions.clear()
            num = graph.renumerate(machine[0])
            trans = ["%d -> %d : %s" % (num.get_id(x[0]+1), num.get_id(x[1]+1), conditionname(x[2])) for x in machine[0]]
            self.ui.listTransitions.insertItems(0, QtCore.QStringList(trans))

            self.ui.listSignalsMachine.clear()
            nodes = sorted("%4d: %s" % (num.get_id(k+1),conditionname(x)) for k,x in machine[1].iteritems())
            self.ui.listSignalsMachine.insertItems(0, QtCore.QStringList(nodes))

        if self.model:
            if len(self.model.barenodes) < 10:
                matrix = ""
                for i in self.model.matrix:
                    matrix += ','.join(["%6s" % (x) for x in i]) + "\n"
                self.log(matrix)

            # model = QtCode.QStandartItemModel(2,3,self)
            model = MatrixModel(self.ui.matrix, self.model)
            self.ui.matrix.setModel(model)
            self.ui.matrix.resizeColumnsToContents()

            self.ui.listLoops.clear()
            node_names = {k:nodename(k, {k: x}) for k,x in self.model.barenodes.iteritems()}
            lines = ['->'.join([node_names[i+1] for i in l]) for l in self.model.find_loops()]
            self.ui.listLoops.insertItems(0, QtCore.QStringList(lines))

            self.ui.listPaths.clear()
            lines = ['->'.join([node_names[i+1] for i in l]) for l in self.model.find_paths()]
            self.ui.listPaths.insertItems(0, QtCore.QStringList(lines))

        if self.tr_table and self.model:
            jks = mtable.jk(self.tr_table)
            q_count = len(self.tr_table[0].q)
            x_count = len(self.model.in_signals)
            y_count = len(self.model.out_signals)
            
            funcs = [mtable.generate_formula("J_{%d}" % (i+1), jk) for i, jk in enumerate(jks[0])] + \
                    [mtable.generate_formula("J_{%dm}" % (i+1), mtable.minimize(jk, q_count, x_count)) for i, jk in enumerate(jks[0])] + \
                    [mtable.generate_formula("K_{%d}" % (i+1), jk) for i, jk in enumerate(jks[1])] + \
                    [mtable.generate_formula("K_{%dm}" % (i+1), mtable.minimize(jk, q_count, x_count)) for i, jk in enumerate(jks[1])] + \
                    [mtable.generate_formula("Y_{%d}" % (i+1), jk) for i, jk in enumerate(jks[2])] + \
                    [mtable.generate_formula("Y_{%dm}" % (i+1), mtable.minimize(jk, q_count, x_count)) for i, jk in enumerate(jks[2])]
            # mtable.latexmath2png.math2png(funcs, os.getcwd(), prefix = "adcs_")

            mtable.latexmath2png.math2png(funcs, os.getcwd(), prefix = "adcs_")

            tr_model = TransitionModel(self.ui.tr_table, self.tr_table, self.model, jks)
            self.ui.tr_table.setModel(tr_model)
            self.ui.tr_table.resizeColumnsToContents()
            self.ui.vhdl_text.setPlainText(vhdl.vhdl(jks, x_count, y_count))

    def _update_graph(self):
        # self.canvas.graph = self.model
        self.log("Drawing...", False)
        if os.path.exists(IMG_PATH):
            self.canvas.setPixmap(QtGui.QPixmap(IMG_PATH))
            self.canvas.adjustSize()
        if os.path.exists(IMG_MACHINE_PATH):
            self.m_canvas.setPixmap(QtGui.QPixmap(IMG_MACHINE_PATH))
            self.m_canvas.adjustSize()
        if os.path.exists(IMG_FORMULAS_PATH):
            self.f_canvas.setPixmap(QtGui.QPixmap(IMG_FORMULAS_PATH))
            self.f_canvas.adjustSize()
        self.log("OK")

    @QtCore.pyqtSlot()
    def validate(self):
        self.model = None
        self.clear_log()
        if os.path.exists(IMG_PATH):
            os.remove(IMG_PATH)
        src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
        self.log("Processing %s" % src)
        self.ui.info.setPlainText("")
        with warnings.catch_warnings(record=True) as warn:
            warnings.simplefilter("always")
            try:
                p = self._process(src)
                self.model = p
            except analysis.LSAAlgorithmError, e:
                self.ui.statusBar.showMessage("Algorithm error:" + e.message)
                self.log("Failed\nAlgorithm error:" + e.message)
                self.ui.info.setPlainText("Algorithm error:" + e.message)
                return
            except parse.LSASyntaxError, e:
                if hasattr(e, "pos"):
                    self.ui.textEdit.moveCursor(QtGui.QTextCursor.StartOfLine)
                    for i in range(e.pos):
                        self.ui.textEdit.moveCursor(QtGui.QTextCursor.Right)
                    self.ui.textEdit.moveCursor(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)
                self.ui.statusBar.showMessage("Syntax error " + e.message)
                self.log("Failed\Syntax error:" + e.message)
                self.ui.info.setPlainText("Syntax error:" + e.message)
                return

            if warn:
                e = warn[-1].message
                self.ui.statusBar.showMessage("Algorithm warning:" + e.message)
                self.log("OK with warnings\nAlgorithm warning:" + e.message)
                self.ui.info.setPlainText("Algorithm warning:" + e.message)
            else:
                self.machine = machine.make_machine(self.model.matrix, self.model.barenodes)
                self.machine = machine.encode_machine(*self.machine)
                print self.machine
                self.tr_table = mtable.build_table(*self.machine)
                self.ui.statusBar.showMessage("OK")

        self._updateMode()

    def _prevSymbol(self):
        store_cursor = self.ui.textEdit.textCursor()
        self.ui.textEdit.moveCursor(QtGui.QTextCursor.Left)
        self.ui.textEdit.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        prev_symbol = str(self.ui.textEdit.textCursor().selectedText().toUtf8()).decode('utf-8')
        self.ui.textEdit.setTextCursor(store_cursor)
        return prev_symbol

    def _convert_key(self, pressed, prev_symbol):
        val = INPUT_KEYS[pressed]
        print "Convert: %s %s [%s]" % (pressed, prev_symbol, val)

        # new number
        if pressed.isdigit() and len(prev_symbol):
            if prev_symbol in [ARROW_UP, ARROW_DOWN]:
                val = SUPERSCRIPT[int(pressed)]
            elif prev_symbol in [SYMB_X, SYMB_Y]:
                val = SUBSCRIPT[int(pressed)]
            elif ord(prev_symbol) in SUPERSCRIPT.values():
                    # continuation of superscript
                    char = SUPERSCRIPT[int(pressed)]
                    val = unichr(char)
            elif ord(prev_symbol) in SUBSCRIPT.values():
                    # continuation of subscript
                    char = SUBSCRIPT[int(pressed)]
                    val = unichr(char)
        return val

    def eventFilter(self, target, event):
        if(event.type() == QtCore.QEvent.KeyPress):
            print "Key presssed " + str(event.text())
            # import ipydb; ipydb.db()
            symb = str(event.text().toUtf8())
            prev_symb = self._prevSymbol()

            if symb in string.printable:
                if symb in INPUT_KEYS:
                    print_symbol = self._convert_key(symb, prev_symb)
                    print print_symbol
                    nevent = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyPress, 0,
                        QtCore.Qt.KeyboardModifiers(0), QtCore.QString(print_symbol))
                    self.ui.textEdit.keyPressEvent(nevent)
                elif symb in string.whitespace:
                    self.ui.textEdit.keyPressEvent(event)
            else:
                self.ui.textEdit.keyPressEvent(event)
            return True
        return False

