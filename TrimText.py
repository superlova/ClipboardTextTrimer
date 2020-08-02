# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from trim import Trim_Clipboard

if __name__ == '__main__':

    app = QApplication(sys.argv)
    trim_clipboard = Trim_Clipboard()
    sys.exit(app.exec_())
