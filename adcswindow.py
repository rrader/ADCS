import string

from PyQt4 import uic
from PyQt4 import QtCore, QtGui

import analysis
from consts import *

(Ui_ADCSWindow, QMainWindow) = uic.loadUiType('adcswindow.ui')

def upper_index(num):
    symbol_index = SUPERSCRIPT[num]
    return unichr(symbol_index)


def lower_index(num):
    symbol_index = SUBSCRIPT[num]
    return unichr(symbol_index)


class ADCSWindow (QMainWindow):
    """ADCSWindow inherits QMainWindow"""
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = Ui_ADCSWindow()
        self.ui.setupUi(self)
        self.connect(self.ui.toolButton_Start,
                     QtCore.SIGNAL('clicked()'), QtCore.SLOT('test_unicode()'))
        self.connect(self.ui.toolButton_Validate,
                     QtCore.SIGNAL('clicked()'), QtCore.SLOT('validate()'))
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
        src = self.ui.textEdit.toPlainText().toUtf8()
        print src
        analysis.validate(src)

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

