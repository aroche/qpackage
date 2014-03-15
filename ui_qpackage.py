# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_qpackage.ui'
#
# Created: Sat Mar 15 20:39:58 2014
#      by: PyQt4 UI code generator 4.10.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_qpackage(object):
    def setupUi(self, qpackage):
        qpackage.setObjectName(_fromUtf8("qpackage"))
        qpackage.resize(583, 412)
        self.verticalLayout_2 = QtGui.QVBoxLayout(qpackage)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lineEdit = QtGui.QLineEdit(qpackage)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.horizontalLayout.addWidget(self.lineEdit)
        self.browseButton = QtGui.QPushButton(qpackage)
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.horizontalLayout.addWidget(self.browseButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tableView = QtGui.QTableView(qpackage)
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.verticalLayout.addWidget(self.tableView)
        self.buttonBox = QtGui.QDialogButtonBox(qpackage)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.retranslateUi(qpackage)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), qpackage.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), qpackage.reject)
        QtCore.QMetaObject.connectSlotsByName(qpackage)

    def retranslateUi(self, qpackage):
        qpackage.setWindowTitle(_translate("qpackage", "qpackage", None))
        self.browseButton.setText(_translate("qpackage", "Browse...", None))

