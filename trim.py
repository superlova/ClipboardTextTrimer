import sys, re, pyperclip
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QPushButton, QTextEdit, QMessageBox
from PyQt5.uic import loadUi
from translator import BaiduTranslator

class Trim_Clipboard(QMainWindow):
    def __init__(self, parent = None):
        super(Trim_Clipboard, self).__init__(parent)
        loadUi('trim.ui', self)
        # self.transEngine = self.comboBox.currentText() # 翻译引擎
        self.trimBtn.clicked.connect(self.onClickTrimBtn) # 绑定trimBtn
        self.formatBtn.clicked.connect(self.onClickFormatBtn) # 绑定formatBtn
        self.copyBtn.clicked.connect(self.onClickCopyRawBtn) # 绑定
        self.clearBtn.clicked.connect(self.onClickClearBtn)
        self.copyTransBtn.clicked.connect(self.onClickCopyTransBtn)
        self.transBtn.clicked.connect(self.onClickTransBtn)
        # self.comboBox.currentIndexChanged.connect(self.comboSelectionChanged)
        self.show()

    @staticmethod
    def trim_txt(text):
        pat1 = re.compile(r'-\n')
        pat2 = re.compile(r'\n')
        # text = str(text).strip() # 转成字符串
        text, n1 = pat1.subn(r'', text)  # 行尾-替换成""空串
        text, n2 = pat2.subn(r' ', text)  # 行尾换行替换成" "空格
        return text, n1, n2

    @staticmethod
    def format_txt(text):
        pat = re.compile(r'\. ([A-Z])')  # 句子的末尾
        text, n = pat.subn(r'.\n\n\1', text)
        return text, n

    @staticmethod
    def trans_txt_baidu(text):
        t = BaiduTranslator()
        r = t.translate('auto', 'zh-CN', text)
        text = r['translation']
        return text

    def onClickTrimBtn(self):
        rawText = self.rawTextEdit.toPlainText() # 取左栏文字
        editedText, n1, n2 = self.trim_txt(rawText) # 执行转换
        self.rawTextEdit.setPlainText(editedText) # 放回左栏
        self.statusBar().showMessage("replace \"-\" {} times, \"\\r\\n\" {} times.".format(n1, n2)) # 在状态栏停留五秒信息

    def onClickFormatBtn(self):
        rawText = self.rawTextEdit.toPlainText() # 取左栏文字
        editedText, n = self.format_txt(rawText) # 执行转换
        self.rawTextEdit.setPlainText(editedText) # 放回左栏
        self.statusBar().showMessage("replace \".\" {} times.".format(n)) # 在状态栏停留五秒信息

    def onClickCopyRawBtn(self):
        rawText = self.rawTextEdit.toPlainText()  # 取左栏文字
        pyperclip.copy(rawText)
        self.statusBar().showMessage("Copied {} characters.".format(len(rawText)))  # 在状态栏停留五秒信息

    def onClickCopyTransBtn(self):
        rawText = self.transEdit.toPlainText()  # 取右栏文字
        pyperclip.copy(rawText)
        self.statusBar().showMessage("Copied {} characters.".format(len(rawText)))  # 在状态栏停留五秒信息

    def onClickClearBtn(self):
        self.rawTextEdit.clear()
        self.statusBar().showMessage("Raw Edit Area has been cleaned.")  # 在状态栏停留五秒信息

    def onClickTransBtn(self):
        transEngine = self.comboBox.currentText() # 翻译引擎
        rawText = self.rawTextEdit.toPlainText()  # 取左栏文字
        # TODO
        if transEngine == 'baidu':
            text = self.trans_txt_baidu(rawText)
            self.transEdit.setPlainText(text)
        else:
            # 信息框
            QMessageBox.information(self, 'Sorry', '目前只支持baidu翻译，其他翻译引擎请等待软件完善', QMessageBox.Yes)

    def comboSelectionChanged(self, index):

        # 输出选项集合中每个选项的索引与对应的内容
        # count()：返回选项集合中的数目
        print('current index', index, 'selection changed', self.comboBox.currentText())
        print('Items in the list are:')
        for count in range(self.comboBox.count()):
            print('Item' + str(count) + '=' + self.comboBox.itemText(count))
