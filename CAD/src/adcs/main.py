import sys

# import PyQt4 QtCore and QtGui modules
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from adcswindow import ADCSWindow

def main():
    # create application
    app = QApplication( sys.argv )
    app.setApplicationName( 'ADCS Lab' )

    # create widget
    w = ADCSWindow()
    w.setWindowTitle( 'ADCS Lab' )
    w.show()

    # connection
    QObject.connect( app, SIGNAL( 'lastWindowClosed()' ), app, SLOT( 'quit()' ) )

    # execute application
    sys.exit( app.exec_() )


if __name__ == '__main__':
    main()
