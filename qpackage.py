# -*- coding: utf-8 -*-
"""
/***************************************************************************
 qpackage
                                 A QGIS plugin
 Creates an export of the project and its data, for easy transfer. Like QConsolidate, but stores all the layers in a single spatialite database and allows custom selection of layers.
                              -------------------
        begin                : 2014-03-12
        copyright            : (C) 2014 by A. Roche
        email                : aroche@photoherbarium.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from qpackagedialog import qpackageDialog
import qpackageproject
import os.path


# A comboBox delegate for changing feature selection mode
class LayerFeatureSelectDelegate(QItemDelegate):
    states = ('all', 'selected', 'displayed')
    
    def createEditor(self, parent, option, index):
        self.editor = QComboBox(parent)
        self.editor.addItems(self.states)
        self.connect(self.editor, SIGNAL("currentIndexChanged(int)"), self, SLOT("currentIndexChanged()"))
        return self.editor
        
    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        val = index.model().data(index)
        editor.setCurrentIndex(self.states.index(val))
        editor.blockSignals(False)
        
    def setModelData(self, editor, model, index):
        model.setData(index, self.states[editor.currentIndex()])
        
    @pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
        

class CandidateLayer:
    def __init__(self, mapLayer):
        self.layer = mapLayer
        self.stored = True
        self.features = 'all'
        
        

class LayersTableModel(QAbstractTableModel):
    headers = ["Save data", "Layer name", "Source", "Save"]
    
    def __init__(self, layerRegistry):
        QAbstractTableModel.__init__(self)
        #self.layerRegistry = layerRegistry
        layers = layerRegistry.mapLayers()
        self.layerIds = layers.keys()
        self.layerData = []
        for id in self.layerIds:
            layer = layers[id]
            # TODO handle defaults according to type
            #if layer.type() == QgsMapLayer.VectorLayer:
                
            self.layerData.append(CandidateLayer(layer))
    
    def columnCount(self, parent):
        return 4
        
    def rowCount(self, parent):
        return len(self.layerData)
        
    def headerData(self, section, orientation, role):
        if (role == Qt.DisplayRole and orientation == Qt.Horizontal):
            return self.headers[section]
            
    def flags(self, index):
        col = index.column()
        res = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if col == 0:
            res = res | Qt.ItemIsEditable | Qt.ItemIsUserCheckable 
        if col == 3:
            res = res | Qt.ItemIsEditable
        return res
            
    def data(self, index, role = Qt.DisplayRole):
        row = index.row()
        col = index.column()
        layer = self.layerData[row].layer
        
        if col == 0 and role == Qt.CheckStateRole:
            if self.layerData[row].stored:
                return Qt.Checked
            else: return Qt.Unchecked
            
        if (col == 1):
            if (role == Qt.DisplayRole):            
                return layer.name()
                
        if col == 2 and role == Qt.DisplayRole:
            return layer.publicSource()
                
        if col == 3 and role == Qt.DisplayRole:
            return self.layerData[row].features
                
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.column() == 0:
            self.layerData[index.row()].stored = value
        if role == Qt.EditRole and index.column() == 3:
            self.layerData[index.row()].features = value
        
        self.emit(SIGNAL("dataChanged"))
        return True 
    
    def countLayersToProcess(self):
        n = 0
        for l in self.layerData:
            if l.stored:
                n += 1
        return n
    
        

class qpackage:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'qpackage_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = qpackageDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/qpackage/icon.png"),
            u"QPackage", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&QPackage", self.action)
        
        self.dlg.tableView.setItemDelegateForColumn(3, LayerFeatureSelectDelegate(self.dlg.tableView))
        

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&QPackage", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def startCopy(self):
        lmodel = self.dlg.tableView.model()
        msgBar = self.iface.messageBar().createMessage("Creating db...")
        progress = QProgressBar()
        progress.setMaximum(lmodel.countLayersToProcess())
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progress.setValue(0)
        msgBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(msgBar, self.iface.messageBar().INFO)
        
        # copy project file
        # temp : 
        filePath = "qpackageTest.qgs"
        projectFile = QgsProject.instance().fileName()
        if filePath == projectFile:
            msg = "Impossible to write on the same file as the project"
            
            return
        
        f = QFile(projectFile)
        if QFile.exists(filePath):
            QFile.remove(filePath)
        f.copy(filePath)  
        
        print os.path.abspath(filePath)
        
        project = qpackageproject.QPackageProject(filePath)
        
        n = 0
        for layer in lmodel.layerData:
            if layer.stored:
                n += 1
                progress.setValue(n)
                msgBar.setText("Copying %s..." % layer.layer.name())
                if layer.layer.type() == QgsMapLayer.VectorLayer:
                    project.copyGenericVectorLayer(layer.layer)
                elif layer.layer.type() == QgsMapLayer.RasterLayer:
                    project.copyRasterLayer(layer.layer)                
                
        project.saveProject()
        
        self.iface.messageBar().clearWidgets()
        
    def createTable(self):
        # populate the table with the layers of the project
        model = LayersTableModel(QgsMapLayerRegistry.instance())
        self.dlg.tableView.setModel(model)

        
    def run(self):
        # show the dialog
        self.createTable()
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            self.startCopy()
            

