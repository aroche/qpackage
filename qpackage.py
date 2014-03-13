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
import os.path


class LayersTableModel(QAbstractTableModel):
    headers = ["Save data", "Layer name", "layer type", "Save"]
    
    def __init__(self, layerRegistry):
        QAbstractTableModel.__init__(self)
        self.layerRegistry = layerRegistry
        layers = layerRegistry.mapLayers()
        self.layerIds = layers.keys()
        self.layerData = []
        for id in self.layerIds:
            layer = layers[id]
            self.layerData.append({'stored': True, 'features': 'all'})
    
    def columnCount(self, parent):
        return 4
        
    def rowCount(self, parent):
        return self.layerRegistry.count()
        
    def headerData(self, section, orientation, role):
        if (role == Qt.DisplayRole and orientation == Qt.Horizontal):
            return self.headers[section]
            
    def data(self, index, role):
        row = index.row()
        col = index.column()
        layer = self.layerRegistry.mapLayer(self.layerIds[row])
        
        if col == 0 and role == Qt.CheckStateRole:
            return Qt.Checked
            
        if (col == 1):
            if (role == Qt.DisplayRole):            
                return layer.name()
            
        


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
        

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&QPackage", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def startCopy(self):
        # copy project file
        projectFile = QgsProject.instance().fileName()
        f = QFile(projectFile)
        newProjectFile = outputDir + "/" + QFileInfo(projectFile).fileName()
        f.copy(newProjectFile)        
        
    def createTable(self):
        # populates the table with the layers of the project
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
            

