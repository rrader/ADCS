import string

from PyQt4 import uic
from PyQt4 import QtCore, QtGui

(Ui_ADCSWindow, QMainWindow) = uic.loadUiType('adcswindow.ui')

SUPERSCRIPT = {
    0: 0x2070,
    1: 0xB9,
    2: 0xB2,
    3: 0xB3,
    4: 0x2074,
    5: 0x2075,
    6: 0x2076,
    7: 0x2077,
    8: 0x2078,
    9: 0x2079,
}

SUBSCRIPT = {
    0: 0x2080,
    1: 0x2081,
    2: 0x2082,
    3: 0x2083,
    4: 0x2084,
    5: 0x2085,
    6: 0x2086,
    7: 0x2087,
    8: 0x2088,
    9: 0x2089,
}

ARROW_UP = unichr(0x2191)
ARROW_DOWN = unichr(0x2193)
SYMB_X = u"X"
SYMB_Y = u"Y"
GROUP_O = u"("
GROUP_C = u")"

INPUT_KEYS = {
    "w": ARROW_UP,
    "s": ARROW_DOWN,
    "x": SYMB_X,
    "y": SYMB_Y,
    "(": GROUP_O,
    ")": GROUP_C,
}

INPUT_KEYS.update(dict(((str(key), unichr(val)) for key, val in SUBSCRIPT.iteritems())))

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
        self.ui.textEdit.installEventFilter(self)

    def __del__(self):
        self.ui = None

    @QtCore.pyqtSlot()
    def test_unicode(self):
        self.ui.textEdit.setHtml(u"<font color=red>123</font>" +
           ARROW_UP.join([upper_index(x) for x in range(0, 10)]) +
           ARROW_DOWN.join([lower_index(x) for x in range(0, 10)]))
        print self.ui.textEdit.toPlainText().toUtf8()

    def _prevSymbol(self):
        store_cursor = self.ui.textEdit.textCursor()
        self.ui.textEdit.moveCursor(QtGui.QTextCursor.Left)
        self.ui.textEdit.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        prev_symbol = str(self.ui.textEdit.textCursor().selectedText().toUtf8()).decode('utf-8')
        self.ui.textEdit.setTextCursor(store_cursor)
        return prev_symbol

    def _convert_key(self, pressed, prev_symbol):
        val = INPUT_KEYS[pressed]
        print "Convert: %s %s" % (pressed, prev_symbol)

        # new number
        if pressed.isdigit() and len(prev_symbol):
            print "digit"
            print type(prev_symbol)
            print type(ARROW_UP)
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
            print prev_symb

            if symb in string.printable:
                if symb in INPUT_KEYS:
                    print_symbol = self._convert_key(symb, prev_symb)
                    nevent = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyPress, 0,
                        QtCore.Qt.KeyboardModifiers(0), QtCore.QString(print_symbol))
                    self.ui.textEdit.keyPressEvent(nevent)
                elif symb in string.whitespace:
                    self.ui.textEdit.keyPressEvent(event)
            else:
                self.ui.textEdit.keyPressEvent(event)
            return True
        return False


class LASEditor(QtGui.QTextEdit):
    def __init__(self, parent=None):
        super(QTextEdit, self).__init__(parent)

