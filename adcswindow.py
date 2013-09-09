import string

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


class ADCSWindow (QMainWindow):
    """ADCSWindow inherits QMainWindow"""
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ADCSWindow()
        self.ui.setupUi(self)
        self.canvas = MyStaticMplCanvas(self)
        self.ui.innerLayout.addWidget(self.canvas)
        # self.connect(self.ui.toolButton_Start,
        #              QtCore.SIGNAL('clicked()'), QtCore.SLOT('test_unicode()'))
        self.ui.actionAnalyse.triggered.connect(self.validate)
        self.ui.textEdit.installEventFilter(self)
        # self.ui.graphTab.enabled = False
        self.ui.textEdit.setPlainText(u'\u25cbX\u2081\u2191\xb9Y\u2081Y\u2082\u2193\xb9Y\u2083\u25cf')

    def __del__(self):
        self.ui = None

    @QtCore.pyqtSlot()
    def test_unicode(self):
        self.ui.textEdit.setHtml(u"<font color=red>123</font>" +
           ARROW_UP.join([upper_index(x) for x in range(0, 10)]) +
           ARROW_DOWN.join([lower_index(x) for x in range(0, 10)]))
        print self.ui.textEdit.toPlainText().toUtf8()

    def clear_log(self):
        self.ui.log.setPlainText(u"")

    def log(self, text, newline=True):
        if newline:
            text = text + "\n"
        self.ui.log.setPlainText(self.ui.log.toPlainText() + text)

    @QtCore.pyqtSlot()
    def validate(self):
        self.clear_log()
        src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
        self.log("Processing %s" % src)
        print src
        try:
            self.log("Parse... ", False)
            parsed = parse.parse(src)
            self.log("OK")
            self.log("Analyse... ", False)
            p = analysis.LSAAnalyser(parsed)
            p.analysis()
            self.log("OK")
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
        
        self.ui.listSignals.clear()
        signals = sorted([conditionname([x]) for x in p.in_signals + p.out_signals])
        self.ui.listSignals.insertItems(0, QtCore.QStringList(signals))

        self.ui.listNodes.clear()
        nodes = sorted([nodename(k, {k: x}) for k,x in p.barenodes.iteritems()])
        self.ui.listNodes.insertItems(0, QtCore.QStringList(nodes))

        print dir(self.ui.matrix) #.setRowCount(10)

        self.canvas.graph = p
        print p.connections
        print p.barenodes
        if len(p.barenodes) < 10:
            matrix = ""
            for i in p.matrix:
                matrix += ','.join(["%6s" % (conditionname(x, uncond=True) if x is not None else '-') for x in i]) + "\n"
            self.log(matrix)

        self.log("Drawing...", False)
        self.canvas.compute_initial_figure()
        self.log("OK")
        self.canvas.fig.canvas.draw()

        # table
        self.ui.info.setPlainText("Input signals: %d\nOutput signals: %d" % (len(p.in_signals), len(p.out_signals)))

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

