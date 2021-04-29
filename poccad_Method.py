##Author github user @Tanneguydv, 2021

import os
import os.path
import sys
from io import StringIO
import contextlib
import traceback
import time
import PyQt5
from qtpy import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, \
    QInputDialog, QFileDialog, QTreeWidgetItem

from OCC.Display.backend import load_backend
load_backend('qt-pyqt5')

import OCC.Display.qtDisplay as qtDisplay

import lib.Scripts as sc
from poccad import Ui_poccad


class Application(PyQt5.QtWidgets.QMainWindow):

    def __init__(self,app, parent=None):

        super(Application, self).__init__(parent)

        self.ui = Ui_poccad()
        self.ui.setupUi(self)

        self.canvas = qtDisplay.qtViewer3d(self)
        self.ui.OCClayout.addWidget(self.canvas)
        self.canvas.resize(829,739)
        self.canvas.InitDriver()
        self.display = self.canvas._display

        #ASSOCIATE Functions to display
        self.ui.render_button.clicked.connect(self.render_file)
        self.ui.isoview_button.clicked.connect(lambda : self.setview('Iso'))
        self.ui.topview_button.clicked.connect(lambda : self.setview('Top'))
        self.ui.leftview_button.clicked.connect(lambda: self.setview('Left'))
        self.ui.frontview_button.clicked.connect(lambda: self.setview('Front'))
        self.ui.rightview_button.clicked.connect(lambda: self.setview('Right'))
        self.ui.bottomview_button.clicked.connect(lambda: self.setview('Bottom'))
        self.ui.rearview_button.clicked.connect(lambda: self.setview('Rear'))

        self.ui.actionNew.triggered.connect(self.new_file)
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_file_as)
        self.ui.actionQuit.triggered.connect(self.quit)
        self.ui.actionAbout.triggered.connect(self.dialog_about)

        self.ui.actionBox.triggered.connect(self.makebox)
        self.ui.actionSphere.triggered.connect(self.makesphere)
        self.ui.actionPoint.triggered.connect(self.makepoint)
        self.ui.actionCut.triggered.connect(self.boolcut)
        self.ui.actionTranslate.triggered.connect(self.translate)
        self.ui.actionStep.triggered.connect(self.exportstep)

        self.changeviewval = 0
        self.render = False

        self.initialize()
        self.ui.OCCedit.setPlainText('from OCC.Extend.DataExchange import read_step_file\n\
block_cylinder_shape = read_step_file("files\cylinder_block.stp")\n\
display.DisplayShape(block_cylinder_shape, update=True)' )
        self.ui.output.appendPlainText('Press F5 to display the Pythonocc-demo step file')
        self.ui.OCCedit.textChanged.connect(self.changetext)

        self.ui.treeWidget.customContextMenuRequested.connect(self.on_contextmenu_tree)
        self.popTreeMenu = QtWidgets.QMenu(self)
        self.popTreeMenu.addAction("double click to display in 'Consult' Tab")

        self.cwd = os.getcwd()
        self.load_project_structure(self.cwd, self.ui.treeWidget)
        self.ui.treeWidget.itemDoubleClicked.connect(self.show_consult)

    def on_contextmenu_tree(self, point):
        self.popTreeMenu.exec_(self.ui.treeWidget.mapToGlobal(point))

    def show_consult(self, item):

        file = item.text(0)
        dir =  ([node.text(0) for node in self.getParents(item)])
        length = len(dir)
        if dir :
            if length == 4 :
                print(str(dir[3])+ '\\' + str(dir[2]) + '\\'+str(dir[1])+ '\\' + str(dir[0]) + '\\'+ str(file))
                consult_file = str(dir[1])+ '\\' + str(dir[0]) +'\\' + str(file)
            if length == 3 :
                print(str(dir[2])+ '\\' +str(dir[1])+ '\\' +str(dir[0]) + '\\'+ str(file))
                consult_file = str(dir[0]) +'\\' + str(file)
            if length == 2 :
                print(str(dir[1])+ '\\' + str(dir[0]) + '\\'+ str(file))
                consult_file = str(dir[1])+ '\\' + str(dir[0]) +'\\' + str(file)
            if length == 1 :
                print(str(dir[0]) + '\\'+ str(file))
                consult_file = str(dir[0]) +'\\' + str(file)
        else :
            print (str(file))
            consult_file = (str(file))
        self.ui.Consult.clear()
        with open (consult_file , 'r') as cf:
            for line in cf :
                self.ui.Consult.appendPlainText(line.strip('\n'))

    def getParents(self, item):
        """
        Return a list containing all parent items of this item.
        The list is empty, if the item is a root item.
        """
        parents = []
        current_item = item
        current_parent = current_item.parent()

        # Walk up the tree and collect all parent items of this item
        while not current_parent is None:
            parents.append(current_parent)
            current_item = current_parent
            current_parent = current_item.parent()
        return parents

    def load_project_structure(self, startpath, tree):
        for element in os.listdir(startpath):
            path_info = startpath + "/" + element
            parent_itm = QTreeWidgetItem(tree, [os.path.basename(element)])
            if os.path.isdir(path_info):
                self.load_project_structure(path_info, parent_itm)
                parent_itm.setIcon(0, QIcon('ui_files\icons\dir.png'))
            else:
                parent_itm.setIcon(0, QIcon('ui_files\icons\\file.png'))

    def changetext(self):
        if self.ui.OCCedit.toPlainText().endswith(':\n'):
            self.ui.OCCedit.insertPlainText('\t')
        if self.ui.OCCedit.toPlainText().endswith('='):
            print ('variable')

    def initialize(self):
        self.box = False
        self.sphere = False
        self.point = False
        self.cut = False
        self.translate = False
        self.expstep = False
        self.file_issaved = False

    def setview(self, view):
        self.ui.activeview.setPixmap(QPixmap('ui_files\icons\\'+ (view) + '_on.png'))
        dispview = 'self.display.View_' + (view)+'()'
        exec (dispview)
        self.display.FitAll()

    def new_file(self):
        self.ui.OCCedit.clear()
        self.display.EraseAll()
        self.initialize()
        self.ui.output.appendPlainText('new codesheet')

    def open_file(self):
        self.initialize()
        self.occ_file_path, _ = PyQt5.QtWidgets.QFileDialog.getOpenFileName(self, 'Select File')
        if self.occ_file_path:
            self.ui.output.appendPlainText('open ' + str(self.occ_file_path))
            self.file_issaved = True
            self.saved_file = (str(self.occ_file_path))
            self.ui.OCCedit.clear()
            with open (self.occ_file_path, "r") as opened_file:
                for line in opened_file:
                    self.ui.OCCedit.appendPlainText(line.strip('\n'))
        else :
            pass

    def save_file(self):
        if self.file_issaved == False :
            self.save_file_as()
        else :
            cad_edit = self.ui.OCCedit.toPlainText()
            self.ui.output.appendPlainText('saving ' + str(self.saved_file))
            with open (self.saved_file, "w") as cfe :
                for line in cad_edit:
                    if line.startswith("display = self.display"):
                        pass
                    if line.startswith('display.FitAll()'):
                        pass
                    else:
                        cfe.writelines(line)

    def save_file_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;occ Files (*.occ)", options=options)
        if self.fileName:
            self.file_issaved = True
            self.saved_file = (str(self.fileName)+'.occ')
            self.ui.output.appendPlainText('saving ' + str(self.saved_file))
            cad_edit = self.ui.OCCedit.toPlainText()
            with open (self.saved_file, "w") as cfe :
                for line in cad_edit:
                    if line.startswith("display = self.display"):
                        pass
                    if line.startswith('display.FitAll()'):
                        pass
                    else:
                        cfe.writelines(line)
        else :
            pass
        
    def render_file(self):
        print('render')
        if os.path.isfile("cad_file_edit.occ"):
            os.remove("cad_file_edit.occ")
        self.display.EraseAll()
        cad_edit = self.ui.OCCedit.toPlainText()
        with open ("cad_file_edit.occ", "a") as cfe :
            cfe.write("display = self.display\n")
            for line in cad_edit:
                if line.startswith("display = self.") :
                    pass
                if line.startswith('display.FitAll()'):
                    pass
                else :
                    cfe.writelines(line)
            cfe.write('\ndisplay.FitAll()')

        try :
            @contextlib.contextmanager
            def stdoutIO(stdout=None):
                old = sys.stdout
                if stdout is None:
                    stdout = StringIO()
                sys.stdout = stdout
                yield stdout
                sys.stdout = old

            with stdoutIO() as s:
                exec(open("cad_file_edit.occ").read())
            self.ui.output.appendPlainText(str(s.getvalue()))
            self.render = True
        except Exception :
            self.ui.output.appendPlainText(str(traceback.format_exc()))

    def dialog_about(self):
        infobox = QtWidgets.QDialog()
        infobox.setObjectName("infobox")
        infobox.resize(671, 379)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ui_files/icons/poccad.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        infobox.setWindowIcon(icon)
        self.logo = QtWidgets.QLabel(infobox)
        self.logo.setGeometry(QtCore.QRect(20, 10, 631, 311))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("readme_files/poccad_github.png"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")
        self.infotext = QtWidgets.QLabel(infobox)
        self.infotext.setGeometry(QtCore.QRect(190, 340, 291, 16))
        self.infotext.setAutoFillBackground(True)
        self.infotext.setScaledContents(False)
        self.infotext.setOpenExternalLinks(True)
        self.infotext.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
        self.infotext.setObjectName("infotext")
        QtCore.QMetaObject.connectSlotsByName(infobox)
        _translate = QtCore.QCoreApplication.translate
        infobox.setWindowTitle(_translate("infobox", "poccad_info"))
        self.infotext.setText(_translate("infobox", "please visit https://github.com/Tanneguydv/poccad"))
        infobox.exec_()

    def quit(self):
        if os.path.isfile("cad_file_edit.occ"):
            os.remove("cad_file_edit.occ")
        sys.exit()

    #PythonOCC functions :
    #Shape

    def makebox(self):
        if self.box == False :
            self.ui.OCCedit.appendPlainText(sc.make_box("imp"))
            self.box = True
        else :
            self.ui.OCCedit.appendPlainText(sc.make_box(''))

    def makesphere(self):
        if self.sphere == False :
            self.ui.OCCedit.appendPlainText(sc.make_sphere("imp"))
            self.sphere = True
        else :
            self.ui.OCCedit.appendPlainText(sc.make_sphere(''))

    #Boolean

    def boolcut(self):
        if self.cut == False :
            self.ui.OCCedit.appendPlainText(sc.bool_cut("imp"))
            self.cut = True
        else :
            self.ui.OCCedit.appendPlainText(sc.bool_cut(''))

    #Transformations

    def translate(self):
        if self.translate == False :
            self.ui.OCCedit.appendPlainText(sc.translate("imp"))
            self.translate = True
        else :
            self.ui.OCCedit.appendPlainText(sc.translate(''))

    #Constrution

    def makepoint(self):
        if self.point == False :
            self.ui.OCCedit.appendPlainText(sc.make_point("imp"))
            self.point = True
        else :
            self.ui.OCCedit.appendPlainText(sc.make_point(''))

    #Exchange

    def exportstep(self):
        if self.expstep == False :
            self.ui.OCCedit.appendPlainText(sc.export_step("imp"))
            self.expstep = True
        else :
            self.ui.OCCedit.appendPlainText(sc.export_step(''))

