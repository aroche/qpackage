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

from PyQt4.QtCore import *
from PyQt4.QtXml import *
from qgis.core import *
from pyspatialite import dbapi2 as db
import os.path


class QPackageProject:
    def __init__(self, projectFile):
        self.projectFile = projectFile
        
        self.loadProject()
        self.createDB()
        
        
    def loadProject(self):
        f = QFile(self.projectFile)
        if not f.open(QIODevice.ReadOnly | QIODevice.Text):
            msg = "Cannot read file %s:\n%s." % (self.projectFile, f.errorString())
            #self.processError.emit(msg)
            return

        self.doc = QDomDocument()
        setOk, errorString, errorLine, errorColumn = self.doc.setContent(f, True)
        if not setOk:
            msg = "Parse error at line %d, column %d:\n%s" % (errorLine, errorColumn, errorString)
            # self.processError.emit(msg)
            print msg
            return False

        f.close()
        
        root = self.doc.documentElement()

        # ensure that relative path used
        e = root.firstChildElement("properties")
        e.firstChildElement("Paths").firstChild().firstChild().setNodeValue("false")

        # get layers section in project
        self.layerElement = root.firstChildElement("projectlayers")
        return True
    
    def saveProject(self):
        f = QFile(self.projectFile)
        if not f.open(QIODevice.WriteOnly | QIODevice.Text):
            msg = "Cannot write file %s:\n%s." % (self.projectFile, f.errorString())
            #self.processError.emit(msg)
            print msg
            return

        out = QTextStream(f)
        self.doc.save(out, 4)
        f.close()
        
    def createDB(self):
        (root, ext) = os.path.splitext(self.projectFile)
        self.slPath = root + '.sqlite'
        # TODO : better way to handle existing db because of time consuming process
        if QFile.exists(self.slPath):
            QFile.remove(self.slPath)
        self.dbConnection = db.connect(self.slPath)
        cur = self.dbConnection.cursor()
        cur.execute("SELECT initspatialmetadata()")
        self.dbConnection.commit()
        
    def copyGenericVectorLayer(self, vLayer):
        crs = vLayer.crs()
        enc = vLayer.dataProvider().encoding()
        layerId = vLayer.id()
        # outFile = "%s/%s.shp" % (self.layersDir, layerName)
        options = ("SPATIAL_INDEX=YES",)
        errmsg = ""
        error = QgsVectorFileWriter.writeAsVectorFormat(vLayer, self.slPath, enc, crs,
            driverName="SQLite", datasourceOptions=("SPATIALITE=YES",),
            newFilename=layerId,
            layerOptions=options, errorMessage=errmsg)
        if error != QgsVectorFileWriter.NoError:
            msg = "Cannot copy layer %s" % layerId
            #self.processError.emit(msg)
            print msg, error
            return

        # update project
        layerNode = self.findLayerInProject(layerId)
        tmpNode = layerNode.firstChildElement("datasource")
        p = "dbname='%s' table='%s' (geometry) sql=" % (self.slPath, layerId)
        tmpNode.firstChild().setNodeValue(p)
        tmpNode = layerNode.firstChildElement("provider")
        tmpNode.setAttribute("encoding", enc)
        tmpNode.firstChild().setNodeValue("spatialite")
        
        
    def findLayerInProject(self, layerId):
        child = self.layerElement.firstChildElement()
        while not child.isNull():
            nm = child.firstChildElement("id")
            if nm.text() == layerId:
                return child
            child = child.nextSiblingElement()
        return None
        
    