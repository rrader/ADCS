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

    def __del__(self):
        self.ui = None

    @QtCore.pyqtSlot()
    def test_unicode(self):
        self.ui.textEdit.setHtml(u"<font color=red>123</font>" +
           ARROW_UP.join([upper_index(x) for x in range(0, 10)]) +
           ARROW_DOWN.join([lower_index(x) for x in range(0, 10)]))
        print self.ui.textEdit.toPlainText().toUtf8()

    @QtCore.pyqtSlot()
    def validate(self):
        src = str(self.ui.textEdit.toPlainText().toUtf8()).decode('utf-8')
        print src
        try:
            p = analysis.LSAAnalyser(parse.parse(src))
            p.analysis()
        except analysis.LSAAlgorithmError, e:
            self.ui.statusBar.showMessage("Algorithm error:" + e.message)
            return
        except parse.LSASyntaxError, e:
            if hasattr(e, "pos"):
                self.ui.textEdit.moveCursor(QtGui.QTextCursor.StartOfLine)
                for i in range(e.pos):
                    self.ui.textEdit.moveCursor(QtGui.QTextCursor.Right)
                self.ui.textEdit.moveCursor(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)
            self.ui.statusBar.showMessage("Syntax error " + e.message)
            return
        print "OK"
        self.ui.statusBar.showMessage("OK")
        self.canvas.graph = p
        self.canvas.compute_initial_figure()
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

