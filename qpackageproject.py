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
        setOk, errorString, errorLine, errorColumn = doc.setContent(f, True)
        if not setOk:
            msg = "Parse error at line %d, column %d:\n%s" % (errorLine, errorColumn, errorString)
            # self.processError.emit(msg)
            return False

        f.close()
        return True
        
    def createDB(self):
        (root, ext) = os.path.splitext(self.projectFile)
        self.dbConnection = db.connect(root + '.sqlite')
        cur = self.dbConnection.cursor()
        cur.execute("SELECT initspatialmetadata()")
        self.dbConnection.commit()
        
        
    def findLayerInProject(self, layerElement, layerName):
        child = layerElement.firstChildElement()
        while not child.isNull():
            nm = child.firstChildElement("layername")
            if nm.text() == layerName:
                return child
            child = child.nextSiblingElement()
        return None
        
    