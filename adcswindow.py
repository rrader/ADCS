import string
import pickle

from PyQt4 import uic
from PyQt4 import QtCore, QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx

import analysis
import parse
import graph
from consts import *

(Ui_ADCSWindow, QMainWindow) = uic.loadUiType('adcswindow.ui')

def upper_index(num):
    symbol_index = SUPERSCRIPT[num]
    return unichr(symbol_index)


def lower_index(num):
    symbol_index = SUBSCRIPT[num]
    return unichr(symbol_index)


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=4, height=4, dpi=70):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        self.graph = None

        self.compute_initial_figure()

        #
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyStaticMplCanvas(MyMplCanvas):
    """Simple canvas with a sine plot."""
    def compute_initial_figure(self):
        if not self.graph:
            G=nx.path_graph(0)
            pos=nx.spring_layout(G)
            nx.draw(G,pos,ax=self.axes)
        else:
            p = self.graph
            graph.draw_graph(p.barenodes, p.connections, ax=self.axes)


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
            value = conditionname(cond, uncond=True) if cond is not None else '-'
        return QtCore.QVariant(value)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.colLabels[section])
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.colLabels[section])
        return QtCore.QVariant()


class ADCSWindow (QMainWindow):
    """ADCSWindow inherits QMainWindow"""
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ADCSWindow()
        self.ui.setupUi(self)
        self.canvas = MyStaticMplCanvas(self)
        self.ui.graphViewTab.addWidget(self.canvas)
        # self.connect(self.ui.toolButton_Start,
        #              QtCore.SIGNAL('clicked()'), QtCore.SLOT('test_unicode()'))
        self.ui.actionAnalyse.triggered.connect(self.validate)
        self.ui.actionSave_alg.triggered.connect(self.save_alg)
        self.ui.actionSave_bin.triggered.connect(self.save_bin)
        self.ui.actionOpen_alg.triggered.connect(self.open_alg)
        self.ui.actionOpen_bin.triggered.connect(self.open_bin)
        self.ui.textEdit.installEventFilter(self)
        # self.ui.graphTab.enabled = False
        self.ui.textEdit.setPlainText(u'\u25cbX\u2081\u2191\xb9Y\u2081Y\u2082\u2193\xb9Y\u2083\u25cf')
        self.model = None
        self._updateMode()

    def __del__(self):
        self.ui = None

    def _updateMode(self):
        # import ipydb; ipydb.db()
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.graphTab), bool(self.model))
        self.ui.tabWidget.setTabEnabled(self.ui.tabWidget.indexOf(self.ui.modelTab), bool(self.model))
        if self.model:
            self._fill_signals()
            self._update_graph()
            self.ui.info.setPlainText("Input signals: %d\nOutput signals: %d" % (len(self.model.in_signals), len(self.model.out_signals)))

    def open_alg(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Algorithm', '', 
                "Algorithm .txt (*.txt)")
        if fname:
            src = open(fname).read().decode('utf-8')
            self.ui.textEdit.setPlainText(src)
            self.model = None
            self.log("file %s loaded (text)" % fname)
        self._updateMode()

    def open_bin(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open Algorithm Model', '', 
                "Algorithm Model .alg (*.alg)")
        if fname:
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
        self.ui.listSignals.clear()
        signals = sorted([conditionname([x]) for x in self.model.in_signals + self.model.out_signals])
        self.ui.listSignals.insertItems(0, QtCore.QStringList(signals))

        self.ui.listNodes.clear()
        nodes = sorted([nodename(k, {k: x}) for k,x in self.model.barenodes.iteritems()])
        self.ui.listNodes.insertItems(0, QtCore.QStringList(nodes))

        if len(self.model.barenodes) < 10:
            matrix = ""
            for i in self.model.matrix:
                matrix += ','.join(["%6s" % (conditionname(x, uncond=True) if x is not None else '-') for x in i]) + "\n"
            self.log(matrix)

        # model = QtCode.QStandartItemModel(2,3,self)
        model = MatrixModel(self.ui.matrix, self.model)
        self.ui.matrix.setModel(model)
        self.ui.matrix.resizeColumnsToContents()


    def _update_graph(self):
        self.canvas.graph = self.model
        self.log("Drawing...", False)
        self.canvas.compute_initial_figure()
        self.log("OK")
        self.canvas.fig.canvas.draw()

    @QtCore.pyqtSlot()
    def validate(self):
        self.clear_log()
        src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
        self.log("Processing %s" % src)
        try:
            p = self._process(src)
            self.model = p
        except analysis.LSAAlgorithmError, e:
            self.ui.statusBar.showMessage("Algorithm error:" + e.message)
            self.log("Failed\nAlgorithm error:" + e.message)
            return
        except parse.LSASyntaxError, e:
            if hasattr(e, "pos"):
                self.ui.textEdit.moveCursor(QtGui.QTextCursor.StartOfLine)
                for i in range(e.pos):
                    self.ui.textEdit.moveCursor(QtGui.QTextCursor.Right)
                self.ui.textEdit.moveCursor(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)
            self.ui.statusBar.showMessage("Syntax error " + e.message)
            self.log("Failed\Syntax error:" + e.message)
            return
        print "OK"
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

